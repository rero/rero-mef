# -*- coding: utf-8 -*-
#
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

from .mef.api import build_ref_string
from ..api import Action, ReroIndexer, ReroMefRecord


class AgentRecord(ReroMefRecord):
    """Agent Record class."""

    name = None

    @classmethod
    def create(cls, data, id_=None, delete_pid=False, dbcommit=False,
               reindex=False, md5=True, **kwargs):
        """Create a new agent record."""
        return super().create(
            data=data,
            id_=id_,
            delete_pid=delete_pid,
            dbcommit=dbcommit,
            reindex=reindex,
            md5=True,
            **kwargs
        )

    def delete(self, force=False, dbcommit=False, delindex=False):
        """Delete agent from MEF record."""
        from .mef.api import AgentMefRecord
        for mef_record in AgentMefRecord.get_mef(self.pid, self.name):
            mef_record.delete_ref(self, dbcommit=dbcommit, reindex=delindex)
        return super().delete(
            force=force,
            dbcommit=dbcommit,
            delindex=delindex
        )

    def create_or_update_mef(self, dbcommit=False, reindex=False,
                             viaf_record=None):
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
        # get all VIAF records
        for viaf in AgentViafRecord.get_viaf(self):
            if viaf.pid not in viaf_pids:
                viaf_pids.add(viaf.pid)
                viaf_records.append(viaf)
        if len(viaf_records) > 1:
            current_app.logger.error(
                f'MULTIPLE VIAF FOUND FOR: {self.name} {self.pid} | '
                f'viaf: {", ".join([viaf.pid for viaf in viaf_records])}'
            )
        # get all VIAF associated MEF records.
        for viaf in viaf_records:
            for mef in AgentMefRecord.get_mef(viaf.pid, viaf.name):
                if mef.pid not in mef_pids:
                    mef_pids.add(mef.pid)
                    mef_records.append(mef)
        # get all MEF records by agent pid
        for mef in AgentMefRecord.get_mef(self.pid, self.name):
            if mef.pid not in mef_pids:
                mef_pids.add(mef.pid)
                mef_records.append(mef)
        if len(mef_records) > 1:
            current_app.logger.error(
                f'MULTIPLE MEF FOUND FOR: {self.name} {self.pid} | '
                f'mef: {", ".join([mef.pid for mef in mef_records])}'
            )

        ref_string = build_ref_string(agent=self.name, agent_pid=self.pid)
        old_pids = set()
        if mef_records:
            # We have MEF records change them.
            for mef in mef_records[1:]:
                # Delete ref in MEF records
                if old_ref := mef.pop(self.name, None):
                    old_pid = old_ref['$ref'].split('/')[-1]
                    if old_pid != self.pid:
                        old_pids.add(old_pid)
                        mef_actions[old_pid] = Action.DELETE
                mef.update(data=mef, dbcommit=dbcommit, reindex=reindex)
                mef_actions[mef.pid] = Action.DISCARD
            # Update first MEF record
            mef_record = mef_records[0]
            if old_ref := mef_record.get(self.name):
                old_pid = old_ref['$ref'].split('/')[-1]
            else:
                old_pid = None
            if old_pid != self.pid:
                if old_pid:
                    old_pids.add(old_pid)
                    mef_actions[old_pid] = Action.DELETE
                mef_record[self.name] = {'$ref': ref_string}
                mef_record = mef_record.update(
                    data=mef_record,
                    dbcommit=dbcommit,
                    reindex=reindex
                )
                mef_actions[mef_record.pid] = Action.UPDATE
            else:
                if reindex:
                    mef_record.reindex()
                mef_actions[mef_record.pid] = Action.UPTODATE
        else:
            # No MEF record create one.
            mef_data = {self.name: {'$ref': ref_string}}
            if self.deleted:
                mef_data['deleted'] = self.deleted
            if viaf_records:
                mef_data['viaf_pid'] = viaf_records[0].pid
            mef_record = AgentMefRecord.create(
                data=mef_data,
                dbcommit=dbcommit,
                reindex=reindex,
            )
            mef_actions[mef_record.pid] = Action.CREATE
        if reindex:
            AgentMefRecord.flush_indexes()
        # create all MEF records for old pids
        for old_pid in old_pids:
            old_rec = self.get_record_by_pid(old_pid)
            mef, action = old_rec.create_or_update_mef(
                dbcommit=True,
                reindex=True
            )
            mef_actions[old_pid] = action
        return mef_record, mef_actions

    @classmethod
    def get_online_record(cls, id, debug=False):
        """Get online Record.

        Has to be overloaded in agent class.

        :param id: Id of online record.
        :param verbose: Verbose print.
        :param debug: Debug print.
        :returns: record or None
        Has to be overloaded in agent class.
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


class AgentIndexer(ReroIndexer):
    """Indexing class for agents."""
