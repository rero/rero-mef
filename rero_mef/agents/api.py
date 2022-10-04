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


import contextlib

import click
from flask import current_app
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_search import current_search

from .mef.api import AgentMefRecord, build_ref_string
from ..api import Action, ReroIndexer, ReroMefRecord
from ..utils import add_md5, add_schema


def get_viaf_by_agent(agent, online=False):
    """Get VIAF record by agent.

    :param agent: Agency do get corresponding VIAF record.
    :param online: Try to get VIAF record online if not exist.
    """
    from .viaf.api import AgentViafRecord, AgentViafSearch
    if isinstance(agent, AgentMefRecord):
        viaf_pid = agent.get('viaf_pid')
        return cls.get_record_by_pid(viaf_pid), False
    if isinstance(agent, AgentViafRecord):
        viaf_pid = agent.get('pid')
        return cls.get_record_by_pid(viaf_pid), False
    pid = agent.get('pid')
    viaf_pid_name = agent.viaf_pid_name
    query = AgentViafSearch() \
        .filter({'term': {viaf_pid_name: pid}})
    if query.count() > 0:
        if query.count() > 1:
            current_app.logger.error(
                f'MULTIPLE VIAF FOUND FOR: {agent.name} {agent.pid}'
            )
        viaf_pid = next(query.source(['pid']).scan()).pid
        return AgentViafRecord.get_record_by_pid(viaf_pid), False
    elif online:
        viaf_data = AgentViafRecord.get_online_viaf_record(
            viaf_source_code=agent.viaf_source_code,
            pid=pid
        )
        if viaf_data:
            viaf_data = add_md5(viaf_data)
            viaf_data = add_schema(
                viaf_data, AgentViafRecord.provider.pid_type)
            viaf_pid = viaf_data.get('pid')
            viaf_record = AgentViafRecord.get_record_by_pid(viaf_pid)
            if viaf_record:
                if viaf_record != viaf_data:
                    viaf_record.replace(data=viaf_data, dbcommit=True,
                                        reindex=True)
                    AgentViafRecord.flush_indexes()
                return viaf_record, False
            viaf_record = AgentViafRecord.create(
                data=viaf_data,
                dbcommit=True,
                reindex=True
            )
            AgentViafRecord.flush_indexes()
            return viaf_record, True
    return None, False


class AgentRecord(ReroMefRecord):
    """Agent Record class."""

    name = None
    agent = None
    viaf_source_code = None

    def __init__(self, *args, **kwargs):
        """Init class."""
        super().__init__(*args, **kwargs)

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
            md5=md5,
            **kwargs
        )

    def create_or_update_mef_viaf_record(self, dbcommit=False, reindex=False,
                                         online=False):
        """Create or update MEF and VIAF record.

        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :param online: Try to get VIAF record online.
        :returns: MEF record, MEF action, VIAF record, VIAF
        """
        from .mef.api import AgentMefRecord
        from .viaf.api import AgentViafRecord
        AgentViafRecord.flush_indexes()
        viaf_record, got_online = get_viaf_by_agent(
            agent=self,
            online=online
        )
        ref_string = build_ref_string(
            agent=self.name,
            agent_pid=self.pid
        )
        mef_data = {self.name: {'$ref': ref_string}}
        mef_record = AgentMefRecord.get_mef_by_entity_pid(self.pid, self.name)
        if viaf_record:
            mef_data['viaf_pid'] = viaf_record.pid
            if not mef_record:
                mef_record = AgentMefRecord.get_mef_by_viaf_pid(
                    viaf_pid=viaf_record.pid
                )
        if self.deleted:
            mef_record, mef_action = self.delete_from_mef(
                dbcommit=dbcommit,
                reindex=reindex
            )
        elif mef_record:
            mef_action = Action.UPDATE
            mef_record = mef_record.update(
                data=mef_data,
                dbcommit=dbcommit,
                reindex=reindex
            )
        else:
            mef_action = Action.CREATE
            mef_record = AgentMefRecord.create(
                data=mef_data,
                dbcommit=dbcommit,
                reindex=reindex
            )
        if reindex:
            AgentMefRecord.flush_indexes()
        return mef_record, mef_action, viaf_record, got_online

    @classmethod
    def flush_indexes(cls):
        """Update indexes."""
        try:
            index = f'agents_{cls.name}'
            current_search.flush_and_refresh(index=index)
        except Exception as err:
            current_app.logger.error(f'ERROR flush and refresh: {err}')

    def delete_from_mef(self, dbcommit=False, reindex=False, verbose=False):
        """Delete agent from MEF record."""
        from .mef.api import AgentMefRecord
        mef_action = Action.DISCARD
        old_mef_pid = 'None'
        mef_record = AgentMefRecord.get_mef_by_entity_pid(self.pid, self.name)
        if mef_record:
            old_mef_pid = mef_record.pid
            if not mef_record.deleted:
                mef_record.pop(self.name, None)
                mef_action = Action.DELETEAGENT
                mef_record = mef_record.replace(
                    data=mef_record,
                    dbcommit=dbcommit,
                    reindex=reindex
                )
                mef_record = AgentMefRecord.create_deleted(
                    record=self,
                    dbcommit=dbcommit,
                    reindex=reindex
                )
            else:
                mef_action = Action.ALREADYDELETED
        else:
            # MEF record is missing create one
            mef_record = AgentMefRecord.create_deleted(
                record=self,
                dbcommit=dbcommit,
                reindex=reindex
            )
            mef_action = Action.CREATE
        if reindex:
            AgentMefRecord.flush_indexes()
        if verbose:
            click.echo(
                f'Delete {self.name}: {self.pid} '
                f'from mef: {old_mef_pid} {mef_action.value} '
                f'new mef: {mef_record.pid}'
            )
        return mef_record, mef_action

    @classmethod
    def create_or_update_agent_mef_viaf(cls, data, id_=None, delete_pid=True,
                                        dbcommit=False, reindex=False,
                                        test_md5=False, online=False,
                                        verbose=False):
        """Create or update agent, MEF and VIAF record."""
        # from rero_mef.agents.mef.api import AgentMefRecord

        with contextlib.suppress(Exception):
            persistent_id = PersistentIdentifier.query.filter_by(
                pid_type=cls.provider.pid_type,
                pid_value=data.get('pid')
            ).one()
            if persistent_id.status == PIDStatus.DELETED:
                return None, Action.ALREADYDELETED, None, Action.DISCARD, \
                    None, False
        record, action = cls.create_or_update(
            data=data,
            id_=id_,
            delete_pid=delete_pid,
            dbcommit=dbcommit,
            reindex=reindex,
            test_md5=test_md5
        )
        if action == Action.ERROR:
            return None, action, None, Action.ERROR, None, False
        if record.deleted:
            mef_record, mef_action = record.delete_from_mef(
                dbcommit=dbcommit,
                reindex=reindex,
                verbose=verbose
            )
            viaf_record = None
            action = Action.DELETE
            online = False
        # elif action == Action.UPTODATE:
        #     mef_record = AgentMefRecord.get_mef_by_entity_pid(
        #         record.pid, record.name)
        #     mef_action = Action.UPTODATE
        #     viaf_record, online = get_viaf_by_agent(
        #         record)
        # else:
        mef_record, mef_action, viaf_record, online_res = \
            record.create_or_update_mef_viaf_record(
                dbcommit=dbcommit,
                reindex=reindex,
                online=online
            )
        return record, action, mef_record, mef_action, viaf_record, online_res

    @classmethod
    def get_online_record(cls, id, verbose=False):
        """Get online Record.

        Has to be overloaded in agent class.
        """
        raise NotImplementedError()

    def reindex(self, forceindex=False):
        """Reindex record."""
        result = super().reindex(forceindex=forceindex)
        if mef := AgentMefRecord.get_mef_by_entity_pid(self.pid, self.name):
            mef.reindex(forceindex=forceindex)
        return result


class AgentIndexer(ReroIndexer):
    """Indexing class for agents."""
