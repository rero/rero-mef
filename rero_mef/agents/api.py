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

from copy import deepcopy

import click
from flask import current_app
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_search import current_search

from ..api import Action, ReroIndexer, ReroMefRecord, ReroMefRecordError
from ..utils import add_md5, add_schema


class AgentRecord(ReroMefRecord):
    """Authority Record class."""

    name = None
    agent = None
    viaf_source_code = None

    def __init__(self, *args, **kwargs):
        """Init class."""
        super().__init__(*args, **kwargs)
        self.agent = self.name

    @classmethod
    def create(cls, data, id_=None, delete_pid=False, dbcommit=False,
               reindex=False, md5=True, **kwargs):
        """Create a new agent record."""
        record = super().create(
            data=data,
            id_=id_,
            delete_pid=delete_pid,
            dbcommit=dbcommit,
            reindex=reindex,
            md5=md5,
            **kwargs
        )
        return record

    @classmethod
    def update_indexes(cls):
        """Update indexes."""
        try:
            index = f'agents_{cls.agent}'
            current_search.flush_and_refresh(index=index)
        except Exception as err:
            current_app.logger.error(f'ERROR flush and refresh: {err}')

    def update_test_md5(self, data, dbcommit=False, reindex=False):
        """Update existing record."""
        return_record = self
        if not data.get('md5'):
            data = add_md5(data)
        if data.get('md5', 'data') == self.get('md5', 'agent'):
            # record has no changes
            return return_record, Action.UPTODATE
        data = add_schema(data, self.agent)
        return_record = self.update(
            data=data, dbcommit=dbcommit, reindex=reindex)
        return return_record, Action.UPDATE

    def replace_test_md5(self, data, dbcommit=False, reindex=False):
        """Replace data in record."""
        new_data = deepcopy(data)
        pid = new_data.get('pid')
        if not pid:
            raise ReroMefRecordError.PidMissing(f'missing pid={self.pid}')
        self.clear()
        self, action = self.update_test_md5(
            data=new_data, dbcommit=dbcommit, reindex=reindex)
        if action == Action.UPTODATE:
            self = new_data
        return self

    def create_or_update_mef_viaf_record(self, dbcommit=False, reindex=False,
                                         online=False):
        """Create or update MEF and VIAF record."""
        from .viaf.api import AgentViafRecord
        AgentViafRecord.update_indexes()
        viaf_record, got_online = AgentViafRecord.get_viaf_by_agent(
            agent=self,
            online=online
        )
        from .mef.api import AgentMefRecord
        ref_string = AgentMefRecord.build_ref_string(
            agent=self.agent,
            agent_pid=self.pid
        )
        mef_data = {self.agent: {'$ref': ref_string}}
        mef_record = AgentMefRecord.get_mef_by_agent_pid(
            agent_pid=self.pid,
            agent_name=self.name
        )
        if viaf_record:
            mef_data['viaf_pid'] = viaf_record.pid
            if not mef_record:
                mef_record = AgentMefRecord.get_mef_by_viaf_pid(
                    viaf_record.pid)
        if self.deleted:
            mef_record, mef_action = self.delete_from_mef(
                dbcommit=dbcommit,
                reindex=reindex
            )
        else:
            if mef_record:
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
                    reindex=reindex,
                )
        if reindex:
            AgentMefRecord.update_indexes()
        return mef_record, mef_action, viaf_record, got_online

    def delete_from_mef(self, dbcommit=False, reindex=False, verbose=False):
        """Delete agent from MEF record."""
        from .mef.api import AgentMefRecord
        mef_action = Action.DISCARD
        old_mef_pid = 'None'
        mef_record = AgentMefRecord.get_mef_by_agent_pid(
            agent_pid=self.pid,
            agent_name=self.name
        )
        if mef_record:
            old_mef_pid = mef_record.pid
            if not mef_record.deleted:
                mef_record.pop(self.agent, None)
                mef_action = Action.DELETEAGENT
                mef_record = mef_record.replace(
                    data=mef_record,
                    dbcommit=dbcommit,
                    reindex=reindex
                )
                mef_record = AgentMefRecord.create_deleted(
                    agent=self,
                    dbcommit=dbcommit,
                    reindex=reindex
                )
            else:
                mef_action = Action.ALREADYDELETED
        else:
            # MEF record is missing create one
            mef_record = AgentMefRecord.create_deleted(
                agent=self,
                dbcommit=dbcommit,
                reindex=reindex
            )
            mef_action = Action.CREATE
        if reindex:
            AgentMefRecord.update_indexes()
        if verbose:
            click.echo(
                f'Delete {self.agent}: {self.pid} '
                f'from mef: {old_mef_pid} {mef_action.value} '
                f'new mef: {mef_record.pid}'
            )
        return mef_record, mef_action

    @classmethod
    def create_or_update_agent_mef_viaf(cls, data, id_=None, delete_pid=True,
                                        dbcommit=False, reindex=False,
                                        test_md5=False, online=False,
                                        verbose=False):
        """Create or update agent, Mef and Viaf record."""
        from rero_mef.agents.mef.api import AgentMefRecord
        from rero_mef.agents.viaf.api import AgentViafRecord

        try:
            persistent_id = PersistentIdentifier.query.filter_by(
                pid_type=cls.provider.pid_type,
                pid_value=data.get('pid')
            ).one()
            if persistent_id.status == PIDStatus.DELETED:
                return None, Action.ALREADYDELETED, None, Action.DISCARD, \
                    None, False
        except Exception:
            pass

        record, action = cls.create_or_update(
            data=data,
            id_=id_,
            delete_pid=delete_pid,
            dbcommit=dbcommit,
            reindex=reindex,
            test_md5=test_md5
        )
        if record.deleted:
            mef_record, mef_action = record.delete_from_mef(
                dbcommit=dbcommit,
                reindex=reindex,
                verbose=verbose
            )
            # record.delete(
            #     dbcommit=dbcommit,
            #     delindex=True,
            # )
            # record = None
            action = Action.DELETE
            viaf_record = None
            online = False
        else:
            if action == Action.UPTODATE:
                mef_record = AgentMefRecord.get_mef_by_agent_pid(
                    agent_pid=record.pid,
                    agent_name=record.name
                )
                mef_action = Action.UPTODATE
                viaf_record, online = AgentViafRecord.get_viaf_by_agent(record)
            else:
                mef_record, mef_action, viaf_record, online = \
                    record.create_or_update_mef_viaf_record(
                        dbcommit=dbcommit,
                        reindex=reindex,
                        online=online
                    )
        return record, action, mef_record, mef_action, viaf_record, online

    @classmethod
    def get_online_record(cls, id, verbose=False):
        """Get online Record.

        Has to be overloaded in agent class.
        """

    @property
    def deleted(self):
        """Get record deleted value."""
        return self.get('deleted')


class AgentIndexer(ReroIndexer):
    """Indexing class for agents."""
