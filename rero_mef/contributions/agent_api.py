# -*- coding: utf-8 -*-
#
# This file is part of RERO MEF.
# Copyright (C) 2018 RERO.
#
# RERO MEF is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO MEF is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO MEF; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""API for manipulating records."""

from copy import deepcopy

import click

from .api import Action, ContributionIndexer, ContributionRecord, \
    ContributionRecordError
from .utils import add_md5, add_schema


class AgentRecord(ContributionRecord):
    """Authority Record class."""

    @classmethod
    def create(cls, data, id_=None, delete_pid=False, dbcommit=False,
               reindex=False, md5=True, **kwargs):
        """Create a new agent record."""
        record = super(AgentRecord, cls).create(
            data=data,
            id_=id_,
            delete_pid=delete_pid,
            dbcommit=dbcommit,
            reindex=reindex,
            md5=md5,
            **kwargs
        )
        return record

    def update_test_md5(self, data, dbcommit=False, reindex=False):
        """Update existing record."""
        return_record = self
        if data.get('md5'):
            data = add_md5(data)
            data_md5 = data.get('md5', 'data')
            agent_md5 = self.get('md5', 'agent')
            if data_md5 == agent_md5:
                # record has no changes
                agent_action = Action.UPTODATE
                return return_record, agent_action
        data = add_schema(data, self.agent)
        return_record = self.update(
            data=data, dbcommit=dbcommit, reindex=reindex)
        agent_action = Action.UPDATE
        return return_record, agent_action

    def replace_test_md5(self, data, dbcommit=False, reindex=False):
        """Replace data in record."""
        new_data = deepcopy(data)
        pid = new_data.get('pid')
        if not pid:
            raise ContributionRecordError.PidMissing(
                'missing pid={pid}'.format(pid=self.pid)
            )
        self.clear()
        self, action = self.update_test_md5(
            data=new_data, dbcommit=dbcommit, reindex=reindex)
        if action == Action.UPTODATE:
            self = new_data
        return self

    def create_or_update_mef_viaf_record(self, dbcommit=False, reindex=False,
                                         online=True):
        """Create or update MEF and VIAF record."""
        from .viaf.api import ViafRecord
        ViafRecord.update_indexes()
        viaf_record, got_online = ViafRecord.get_viaf_by_agent(
            agent=self,
            online=online
        )
        from .mef.api import MefRecord
        ref_string = MefRecord.build_ref_string(
            agent=self.agent,
            agent_pid=self.pid
        )
        mef_data = {self.agent: {'$ref': ref_string}}
        if viaf_record:
            mef_data['viaf_pid'] = viaf_record.pid
            mef_record = MefRecord.get_mef_by_viaf_pid(viaf_record.pid)
        else:
            mef_record = MefRecord.get_mef_by_agent_pid(self.pid, self.agent)
        if self.deleted:
            if mef_record:
                mef_action = Action.DELETEAGENT
                mef_record.pop(self.agent, None)
                mef_record = mef_record.update(
                    data=mef_record,
                    dbcommit=dbcommit,
                    reindex=reindex
                )
            else:
                mef_action = Action.DISCARD
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
                mef_record = MefRecord.create(
                    data=mef_data,
                    dbcommit=dbcommit,
                    reindex=reindex,
                )
        if reindex:
            MefRecord.update_indexes()
        return mef_record, mef_action, viaf_record, got_online

    @classmethod
    def create_or_update_agent_mef_viaf(cls, data, id_=None, delete_pid=True,
                                        dbcommit=False, reindex=False,
                                        test_md5=False, online=True):
        """Create or update agent, Mef and Viaf record."""
        record, action = cls.create_or_update(
            data=data,
            id_=id_,
            delete_pid=delete_pid,
            dbcommit=dbcommit,
            reindex=reindex,
            test_md5=test_md5,
            online=online
        )
        mef_record, mef_action, viaf_record, online = \
            record.create_or_update_mef_viaf_record(
                dbcommit=dbcommit,
                reindex=reindex,
                online=online
            )
        return record, action, mef_record, mef_action, viaf_record, online

    def delete_from_mef(self, dbcommit=False, reindex=False, verbose=False):
        """Delete agent from MEF record."""
        from .mef.api import MefRecord
        action = Action.DISCARD
        mef_pid = 'Non'
        mef_record = MefRecord.get_mef_by_agent_pid(self.pid, self.agent)
        if mef_record:
            mef_pid = mef_record.pid
            if mef_record.pop(self.agent, None):
                action = Action.UPDATE
                mef_record = mef_record.replace(
                    data=mef_record,
                    dbcommit=dbcommit,
                    reindex=reindex
                )
                if reindex:
                    MefRecord.update_indexes()
        if verbose:
            click.echo(
                'Delete {agent}: {pid} from MEF: {mef_pid}  {action}'.format(
                    agent=self.agent,
                    pid=self.pid,
                    mef_pid=mef_pid,
                    action=action
                )
            )
        return action

    @classmethod
    def get_online_record(cls, id, verbose=False):
        """Get online Record.

        Has to be overloaded in agent class.
        """
        return None

    @property
    def deleted(self):
        """Get record deleted value."""
        return self.get('deleted')


class AgentIndexer(ContributionIndexer):
    """Indexing class for agents."""
