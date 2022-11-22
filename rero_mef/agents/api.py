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

    def create_or_update_mef(self, dbcommit=False, reindex=False):
        """Create or update MEF.

        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :returns: MEF record, MEF action
        """
        from rero_mef.agents import AgentMefRecord, AgentViafRecord

        mef_data = {}
        viaf_record = {}
        update = False
        # Try to get MEF by VIAF
        if viaf_records := AgentViafRecord.get_viaf(self):
            viaf_record = viaf_records[0]
            if mef_records := AgentMefRecord.get_mef(
                    viaf_record.pid, viaf_record.name):
                mef_data = mef_records[0]
                update = True
        # No MEF by VIAF found try to get MEF by agent
        if not update:
            if mef_records := AgentMefRecord.get_mef(self.pid, self.name):
                mef_data = mef_records[0]
                update = True

        if self.deleted and not mef_data.get('deleted'):
            mef_data['deleted'] = self.deleted

        ref_string = build_ref_string(agent=self.name, agent_pid=self.pid)
        mef_data[self.name] = {'$ref': ref_string}

        if viaf_record:
            mef_data['viaf_pid'] = viaf_record['pid']
        if update:
            mef_action = Action.UPDATE
            mef_record = mef_data.replace(
                data=mef_data,
                dbcommit=dbcommit,
                reindex=reindex
            )
        else:
            mef_action = Action.CREATE
            mef_record = AgentMefRecord.create(
                data=mef_data,
                dbcommit=dbcommit,
                reindex=reindex,
            )
        if reindex:
            AgentMefRecord.flush_indexes()
        return mef_record, mef_action

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
