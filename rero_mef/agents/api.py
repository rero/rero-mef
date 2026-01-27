# RERO MEF
# Copyright (C) 2020 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""API for manipulating records."""

from flask import current_app

from rero_mef.utils import build_ref_string

from ..api import Action, EntityIndexer, EntityRecord


class AgentRecord(EntityRecord):
    """Agent Record class."""

    name = None

    @classmethod
    def create(
        cls,
        data,
        id_=None,
        delete_pid=False,
        dbcommit=False,
        reindex=False,
        md5=True,
        **kwargs,
    ):
        """Create a new agent record."""
        return super().create(
            data=data,
            id_=id_,
            delete_pid=delete_pid,
            dbcommit=dbcommit,
            reindex=reindex,
            md5=md5,
            **kwargs,
        )

    def delete(self, force=False, dbcommit=False, delindex=False):
        """Delete agent from MEF record."""
        from .mef.api import AgentMefRecord

        for mef_record in AgentMefRecord.get_mef(self.pid, self.name):
            mef_record.delete_ref(self, dbcommit=dbcommit, reindex=delindex)
        return super().delete(force=force, dbcommit=dbcommit, delindex=delindex)

    def create_or_update_mef(self, dbcommit=False, reindex=False, viaf_record=None):
        """Create or update MEF.

        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :param viaf_record: VIAF record to use if we know it before.
        :returns: MEF record, MEF action
        """
        from rero_mef.agents import AgentMefRecord, AgentViafRecord

        mef_records = []
        mef_pids = set()
        mef_actions = {}
        viaf_records = [viaf_record] if viaf_record else []
        viaf_pids = {viaf_record.pid} if viaf_record else set()
        # Collect all VIAF records linked to this agent to ensure we find
        # all related MEF records (agents can be linked to multiple VIAF records)
        for viaf in AgentViafRecord.get_viaf(self):
            if viaf.pid not in viaf_pids:
                viaf_pids.add(viaf.pid)
                viaf_records.append(viaf)
        if len(viaf_records) > 1:
            current_app.logger.error(
                f"MULTIPLE VIAF FOUND FOR: {self.name} {self.pid} | "
                f"viaf: {', '.join([viaf.pid for viaf in viaf_records])}"
            )
        # Collect all MEF records associated with found VIAF records
        # This ensures we don't create duplicate MEF records
        for viaf in viaf_records:
            for mef in AgentMefRecord.get_mef(viaf.pid, viaf.name):
                if mef.pid not in mef_pids:
                    mef_pids.add(mef.pid)
                    mef_records.append(mef)
        # Also collect MEF records directly linked to this agent by PID
        for mef in AgentMefRecord.get_mef(self.pid, self.name):
            if mef.pid not in mef_pids:
                mef_pids.add(mef.pid)
                mef_records.append(mef)
        if len(mef_records) > 1:
            current_app.logger.error(
                f"MULTIPLE MEF FOUND FOR: {self.name} {self.pid} | "
                f"mef: {', '.join([mef.pid for mef in mef_records])}"
            )

        ref_string = build_ref_string(
            entity_type="agents", entity_name=self.name, entity_pid=self.pid
        )
        old_pids = set()
        if mef_records:
            # Multiple MEF records found: consolidate them
            # Keep the first MEF record and merge/discard the others
            for mef in mef_records[1:]:
                # Remove this agent's reference from duplicate MEF records
                if old_ref := mef.pop(self.name, None):
                    old_pid = old_ref["$ref"].split("/")[-1]
                    # Track old PIDs that need new MEF records created
                    if old_pid != self.pid:
                        old_pids.add(old_pid)
                        mef_actions[old_pid] = Action.DELETE
                mef.update(data=mef, dbcommit=dbcommit, reindex=reindex)
                mef_actions[mef.pid] = Action.DISCARD
            # Update first MEF record
            mef_record = mef_records[0]
            if old_ref := mef_record.get(self.name):
                old_pid = old_ref["$ref"].split("/")[-1]
            else:
                old_pid = None
            if old_pid != self.pid:
                if old_pid:
                    old_pids.add(old_pid)
                    mef_actions[old_pid] = Action.DELETE
                mef_record[self.name] = {"$ref": ref_string}
            mef_record.set_deleted()
            mef_record = mef_record.update(
                data=mef_record, dbcommit=dbcommit, reindex=reindex
            )
            mef_actions[mef_record.pid] = Action.UPDATE
        else:
            # No MEF record create one.
            mef_data = {self.name: {"$ref": ref_string}}
            if self.deleted and not mef_data.get("deleted"):
                mef_data["deleted"] = self.deleted
            if viaf_records:
                mef_data["viaf_pid"] = viaf_records[0].pid
            mef_record = AgentMefRecord.create(
                data=mef_data,
                dbcommit=dbcommit,
                reindex=reindex,
            )
            mef_actions[mef_record.pid] = Action.CREATE
        if reindex:
            AgentMefRecord.flush_indexes()
        # Recreate MEF records for agents that were removed during consolidation.
        # This ensures agents that were previously in duplicate MEF records
        # still have their own MEF records after consolidation.
        # dbcommit=True and reindex=True are intentionally hardcoded here:
        # the new MEF records must be persisted and indexed immediately so that
        # subsequent calls to create_or_update_mef for other agents can see them
        # and avoid creating further duplicates. Using the caller's flags could
        # leave these records invisible within the same transaction.
        # Recursion depth is bounded: old_pids are agents that were displaced
        # from a duplicate MEF record; once they get their own fresh MEF record
        # (no existing duplicates to consolidate), the recursion terminates.
        for old_pid in old_pids:
            old_rec = self.get_record_by_pid(old_pid)
            mef, action = old_rec.create_or_update_mef(dbcommit=True, reindex=True)
            mef_actions[old_pid] = action
        return mef_record, mef_actions

    @classmethod
    def get_online_record(cls, id_, debug=False):
        """Get online Record.

        :param id_: Id of online record.
        :param debug: Debug print.
        :returns: record or None
        :raises NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError()

    def reindex(self, forceindex=False):
        """Reindex record."""
        from .mef.api import AgentMefRecord

        result = super().reindex(forceindex=forceindex)
        # reindex MEF records
        for mef_record in AgentMefRecord.get_mef(self.pid, self.name):
            mef_record.reindex(forceindex=forceindex)
        return result


class AgentIndexer(EntityIndexer):
    """Indexing class for agents."""
