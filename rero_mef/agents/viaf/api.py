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

"""API for manipulating VIAF record."""

import click
import requests
from elasticsearch_dsl.query import Q
from flask import current_app
from invenio_search.api import RecordsSearch

from .fetchers import viaf_id_fetcher
from .minters import viaf_id_minter
from .models import ViafMetadata
from .providers import ViafProvider
from ..api import Action, ReroIndexer, ReroMefRecord
from ..mef.api import AgentMefRecord
from ..utils import get_entity_class
from ...utils import get_entity_class, progressbar, requests_retry_session


class AgentViafSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'viaf'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class AgentViafRecord(ReroMefRecord):
    """VIAF agent class."""

    minter = viaf_id_minter
    fetcher = viaf_id_fetcher
    provider = ViafProvider
    name = 'viaf'
    model_cls = ViafMetadata
    search = AgentViafSearch

    def create_mef_and_agents(self, dbcommit=False, reindex=False,
                              online=None, verbose=False,
                              online_verbose=False):
        """Create MEF and agents records.

        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :param online: Search online for new VIAF record.
        :param verbose: Verbose.
        :param online_verbose: Online verbose
        :returns: Actions.
        """
        actions = {}
        mef_actions = {}
        online = online or []
        for agent in self.get_agents_pids():
            agent_record = None
            action = Action.UPTODATE
            agent_class = agent['record_class']
            pid = agent['pid']
            if agent_class.provider.pid_type in online:
                data, msg = agent_class.get_online_record(id=pid)
                if online_verbose:
                    click.echo(msg)
                if data and not data.get('NO TRANSFORMATION'):
                    agent_record, action = agent_class.create_or_update(
                        data=data, dbcommit=dbcommit, reindex=reindex)
            else:
                agent_record = agent_class.get_record_by_pid(pid)
            if agent_record:
                mef_record, mef_action = agent_record.create_or_update_mef(
                    dbcommit=dbcommit, reindex=reindex)
                actions[agent_class.name] = {
                    'pid': pid,
                    'action': action.name
                }
                mef_pid = mef_record.pid
                mef_actions.setdefault(mef_pid, []).append(mef_action.name)
            else:
                actions[agent_class.name] = {
                    'pid': pid,
                    'action': 'NOT FOUND'
                }
        if verbose:
            msgs = [
                f'{key}: {value["pid"]} {value["action"]}'
                for key, value in actions.items()
            ]
            mef_msgs = [
                f'{key:<10} {",".join(value)}'
                for key, value in mef_actions.items()
            ]
            click.echo(
                '  Create MEF from VIAF pid: '
                f'{self.pid:<25} '
                f'| MEF: {"; ".join(mef_msgs)} '
                f'| AGENTS: {"; ".join(msgs)}'
            )
        return actions, mef_actions

    def update_mef_and_agents(self, dbcommit=False, reindex=False):
        """Update MEF and agents records.

        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :param verbose: Verbose.
        :returns: Actions.
        """
        agent_records = self.get_agents_records()
        missing_records = []
        for mef_record in AgentMefRecord.get_mef(
                entity_pid=self.pid, entity_name=self.name):
            agent_records_mef = mef_record.get_entities_records()
            for agent_record_mef in agent_records_mef:
                if agent_record_mef not in agent_records:
                    mef_record.pop(agent_record_mef.name)
                    missing_records.append(agent_record_mef)
            # clean other MEF records
            for agent_record in agent_records:
                if agent_record not in agent_records_mef:
                    for other_mef_record in AgentMefRecord.get_mef(
                            entity_pid=agent_record.pid,
                            entity_name=agent_record.name):
                        if other_mef_record.get('viaf_pid') != self.pid:
                            other_mef_record.pop(agent_record.name, None)
                            other_mef_record.update(
                                data=other_mef_record,
                                dbcommit=dbcommit,
                                reindex=reindex
                            )
            mef_record = mef_record.update(
                data=mef_record, dbcommit=dbcommit, reindex=reindex)
            if reindex:
                mef_record.flush_indexes()

        for missing_record in missing_records:
            mef_record, _ = missing_record.create_or_update_mef(
                dbcommit=dbcommit, reindex=reindex)
            if reindex:
                mef_record.flush_indexes()

    def update(self, data, dbcommit=False, reindex=False):
        """Update data in record.

        :param data: a dict data to update the record.
        :param commit: if True push the db transaction.
        :param dbcommit: make the change effective in db.
        :param reindex: reindex the record.
        :returns: the modified record
        """
        self = super().update(data=data, dbcommit=dbcommit, reindex=reindex)
        self.update_mef_and_agents(dbcommit=dbcommit, reindex=reindex)
        return self

    @classmethod
    def create(cls, data, id_=None, delete_pid=False, dbcommit=False,
               reindex=False, md5=False, **kwargs):
        """Create record from data."""
        self = super().create(
            data=data,
            delete_pid=delete_pid,
            dbcommit=dbcommit,
            reindex=reindex,
            md5=md5,
            **kwargs
        )
        self.update_mef_and_agents(dbcommit=dbcommit, reindex=reindex)
        return self

    def reindex(self, forceindex=False):
        """Reindex record."""
        result = super().reindex(forceindex=forceindex)
        self.flush_indexes()
        return result

    @classmethod
    def get_online_record(cls, viaf_source_code, pid, format=None):
        """Get VIAF record.

        Get's the VIAF record from:
        http://www.viaf.org/viaf/sourceID/{source_code}|{pid}

        :param viaf_source_code: agent source code
        :param pid: pid for agent source code
        :param format: raw = get the not transformed VIAF record
                       link = get the VIAF link record
        :returns: VIAF record as json
        """
        source_code = {
            'DNB': 'gnd_pid',
            'SUDOC': 'idref_pid',
            'RERO': 'rero_pid'
        }
        viaf_format = '/viaf.json'
        if format == 'link':
            viaf_format = '/justlinks.json'
            format = 'raw'
        viaf_url = current_app.config.get('RERO_MEF_VIAF_BASE_URL')
        url = (f'{viaf_url}/viaf/sourceID/'
               f'{viaf_source_code}|{pid}{viaf_format}')
        response = requests_retry_session().get(url)
        result = {}
        if response.status_code == requests.codes.ok:
            msg = f'VIAF get: {pid:<15} {url} | OK'
            if format == 'raw':
                return response.json(), msg
            data_json = response.json()
            result['pid'] = data_json['viafID']
            sources = data_json.get('sources', {}).get('source')
            if isinstance(sources, dict):
                sources = [sources]
            for source in sources:
                text = source.get('#text', '|').split('|')
                if text[0] in source_code:
                    result[source_code[text[0]]] = text[1]
        # make sure we got a VIAF with the same pid for source
        if result.get(source_code.get(viaf_source_code)) == pid:
            return result, msg
        return {}, f'VIAF get: {pid:<15} {url} | NO RECORD'

    @classmethod
    def get_viaf(cls, agent):
        """Get VIAF record by agent.

        :param agent: Agency do get corresponding VIAF record.
        :param online: Try to get VIAF record online if not exist.
        """
        if isinstance(agent, AgentMefRecord):
            return [cls.get_record_by_pid(agent.get('viaf_pid'))]
        if isinstance(agent, AgentViafRecord):
            return [cls.get_record_by_pid(agent.get('pid'))]
        pid = agent.get('pid')
        viaf_pid_name = agent.viaf_pid_name
        query = AgentViafSearch() \
            .filter({'term': {viaf_pid_name: pid}}) \
            .params(preserve_order=True) \
            .sort({'_updated': {'order': 'desc'}})
        viaf_records = [
            cls.get_record_by_pid(hit.pid) for hit in
            query.source('pid').scan()
        ]
        if len(viaf_records) > 1:
            current_app.logger.error(
                f'MULTIPLE VIAF FOUND FOR: {agent.name} {agent.pid}'
            )
        return viaf_records

    def delete(self, force=True, dbcommit=False, delindex=False):
        """Delete record and persistent identifier.

        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :returns: MEF actions message.
        """
        agents_records = self.get_agents_records()
        mef_records = AgentMefRecord.get_mef(
            entity_pid=self.pid, entity_name=self.name)
        # delete VIAF record
        result = super().delete(
            force=True, dbcommit=dbcommit, delindex=delindex)
        mef_actions = []
        for mef_record in mef_records:
            # delete associated MEF record
            mef_actions.append(f'Mark as deleted MEF: {mef_record.pid}')
            for agent_record in agents_records:
                mef_record.delete_ref(agent_record)
            mef_record.pop('viaf_pid', None)
            mef_record.mark_as_deleted(dbcommit=True, reindex=True)
        AgentMefRecord.flush_indexes()
        # recreate MEF records for agents
        for agent_record in agents_records:
            mef_record, mef_action = agent_record.create_or_update_mef(
                dbcommit=True, reindex=True)
            mef_actions.append(
                f'{agent_record.name}: {agent_record.pid} '
                f'MEF: {mef_record.pid} {mef_action.value}'
            )
        AgentMefRecord.flush_indexes()
        return result, Action.DELETE, mef_actions

    def get_agents_pids(self):
        """Get agent pids."""
        agents = []
        for agent in current_app.config.get('RERO_AGENTS', []):
            record_class = get_entity_class(agent)
            if record_class.viaf_pid_name in self:
                agents.append({
                    'record_class': record_class,
                    'pid': self.get(record_class.viaf_pid_name)
                })
        return agents

    def get_agents_records(self):
        """Get agent records."""
        agent_records = []
        for agent in self.get_agents_pids():
            record_class = agent['record_class']
            if agent_record := record_class.get_record_by_pid(agent['pid']):
                agent_records.append(agent_record)
        return agent_records

    @classmethod
    def get_missing_agent_pids(cls, agent, verbose=False):
        """Get all missing pids defined in VIAF.

        :param agent: Agent to search for missing pids.
        :param verbose: Verbose.
        :returns: Agent pids without VIAF, VIAF pids without agent
        """
        if record_class := get_entity_class(agent):
            if verbose:
                click.echo(f'Get pids from {agent} ...')
            progress = progressbar(
                items=record_class.get_all_pids(),
                length=record_class.count(),
                verbose=verbose
            )
            pids_db = set(progress)

            agent_pid_name = f'{record_class.name}_pid'
            if verbose:
                click.echo(f'Get pids from VIAF with {agent_pid_name} ...')
            query = AgentViafSearch() \
                .filter('bool', should=[Q('exists', field=agent_pid_name)])
            progress = progressbar(
                items=query.source(['pid', agent_pid_name]).scan(),
                length=query.count(),
                verbose=verbose
            )
            pids_viaf = []
            for hit in progress:
                viaf_pid = hit.pid
                agent_pid = hit.to_dict().get(agent_pid_name)
                if agent_pid in pids_db:
                    pids_db.discard(agent_pid)
                else:
                    pids_viaf.append(viaf_pid)
            return list(pids_db), pids_viaf
        click.secho(f'ERROR Record class not found for: {agent}', fg='red')
        return [], []

    @classmethod
    def get_pids_with_multiple_viaf(cls, verbose=False):
        """Get agent pids with multiple MEF records.

        :params record_types: Record types (pid_types).
        :param verbose: Verbose.
        :returns: pids, multiple pids, missing pids.
        """
        multiple_pids = {
            'gnd_pid': {},
            'idref_pid': {},
            'rero_pid': {}
        }
        progress = progressbar(
            items=AgentViafSearch()
            .params(preserve_order=True)
            .sort({'pid': {'order': 'asc'}})
            .scan(),
            length=AgentViafSearch().count(),
            verbose=verbose
        )
        for hit in progress:
            viaf_pid = hit.pid
            data = hit.to_dict()
            for agent in multiple_pids:
                if pid := data.get(agent):
                    multiple_pids[agent].setdefault(pid, [])
                    multiple_pids[agent][pid].append(viaf_pid)
        cleaned_pids = {
            'gnd_pid': {},
            'idref_pid': {},
            'rero_pid': {}
        }
        for agent, pids in multiple_pids.items():
            for pid, viaf_pids in pids.items():
                if len(viaf_pids) > 1:
                    cleaned_pids[agent][pid] = viaf_pids
        return cleaned_pids


class AgentViafIndexer(ReroIndexer):
    """ViafIndexer."""

    record_class = AgentViafRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, op_type='index', doc_type='viaf')
