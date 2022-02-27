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
from invenio_db import db
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_rest.utils import obj_or_import_string
from invenio_search import current_search
from invenio_search.api import RecordsSearch

from .fetchers import viaf_id_fetcher
from .minters import viaf_id_minter
from .models import ViafMetadata
from .providers import ViafProvider
from ..api import ReroIndexer, ReroMefRecord
from ..mef.api import AgentMefRecord
from ..utils import get_agents_endpoints
from ...utils import get_entity_class, progressbar


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
    model_cls = ViafMetadata

    @classmethod
    def get_online_viaf_record(cls, viaf_source_code, pid, format=None):
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
        url = (f'http://www.viaf.org/viaf/sourceID/'
               f'{viaf_source_code}|{pid}{viaf_format}')
        response = requests.get(url)
        result = {}
        if response.status_code == requests.codes.ok:
            if format == 'raw':
                return response.json()
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
            return result

    @classmethod
    def get_viaf_by_agent(cls, agent, online=False):
        """Get VIAF record by agent.

        :param agent: Agency do get corresponding VIAF record.
        :param online: Try to get VIAF record online if not exist.
        """
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
        try:
            viaf_pid = next(query.source(['pid']).scan()).pid
            return cls.get_record_by_pid(viaf_pid), False
        except StopIteration:
            if online:
                viaf_source_code = agent.viaf_source_code
                viaf_data = cls.get_online_viaf_record(
                    viaf_source_code=viaf_source_code,
                    pid=pid
                )
                if viaf_data:
                    viaf_pid = viaf_data.get('pid')
                    viaf_record = cls.get_record_by_pid(viaf_pid)
                    if viaf_record:
                        viaf_record.reindex()
                        cls.update_indexes()
                        return viaf_record, False
                    viaf_record = cls.create(
                        data=viaf_data,
                        dbcommit=True,
                        reindex=True
                    )
                    cls.update_indexes()
                    return viaf_record, True
        return None, False

    def create_mef_and_agents(self, dbcommit=False, reindex=False,
                              test_md5=False, online=False,
                              verbose=False):
        """Create MEF and agents records.

        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :param test_md5: Test MD% (not used).
        :param online: Search online for new VIAF record.
        :param verbose: Verbose.
        :returns: Actions.
        """
        actions = {}
        for agent, agent_data in get_agents_endpoints().items():
            record_class = obj_or_import_string(agent_data.get('record_class'))
            pid_value = self.get(f'{record_class.name}_pid')
            if pid_value:
                agent_class = obj_or_import_string(
                    agent_data.get('record_class')
                )
                try:
                    PersistentIdentifier.get(
                        agent_class.provider.pid_type,
                        pid_value
                    )
                except PIDDoesNotExistError:
                    # try to get the agent record online
                    if online:
                        data = agent_class.get_online_record(
                            id=pid_value,
                            verbose=verbose
                        )
                        if data:
                            results = \
                                agent_class.create_or_update_agent_mef_viaf(
                                    data=data,
                                    dbcommit=dbcommit,
                                    reindex=reindex,
                                    online=False,
                                    verbose=verbose
                                )
                            pid = 'Non'
                            if results[0]:
                                pid = results[0].pid
                            action = 'UNKNOWN'
                            if results[1]:
                                action = results[1].name
                            m_pid = 'Non'
                            if results[2]:
                                m_pid = results[2].pid
                            m_action = 'UNKNOWN'
                            if results[3]:
                                m_action = results[3].name
                            actions[agent] = {
                                'pid': pid,
                                'action': action,
                                'm_pid': m_pid,
                                'm_action': m_action,
                            }

        if verbose:
            msgs = []
            for key, value in actions.items():
                msgs.append(
                    f'{key}: {value["pid"]} {value["action"]} '
                    f'mef: {value["m_pid"]} {value["m_action"]}'
                )
            if msgs:
                click.echo(
                    f'  Create MEF from VIAF pid: {pid} | {actions}'
                )
        return actions

    @classmethod
    def update_indexes(cls):
        """Update indexes."""
        try:
            current_search.flush_and_refresh(index='viaf')
        except Exception as err:
            current_app.logger.error(f'ERROR flush and refresh: {err}')

    def delete(self, dbcommit=False, delindex=False, online=False):
        """Delete record and persistent identifier.

        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :param online: Search online for new VIAF record.
        :returns: MEF actions message.
        """
        agents_records = self.get_agents_records()
        # delete viaf_pid from MEF record
        mef_record = AgentMefRecord.get_mef_by_viaf_pid(self.pid)
        if mef_record:
            mef_record.pop('viaf_pid', None)
            mef_record.replace(mef_record, dbcommit=dbcommit, reindex=True)
        # delete VIAF record
        persistent_identifier = self.get_persistent_identifier(self.id)
        result = super().delete(force=True)
        if dbcommit:
            self.dbcommit()
        if delindex:
            self.delete_from_index()
            self.update_indexes()
        # realy delete persistent identifier
        db.session.delete(persistent_identifier)
        if dbcommit:
            db.session.commit()

        mef_actions = []
        if mef_record:
            # delete associated MEF record
            mef_record.delete(dbcommit=dbcommit, delindex=delindex)
            # recreate MEF and VIAF records for agents
            for pid_type, agent_record in agents_records.items():
                record, action, mef_record, mef_action, viaf_record, online = \
                    agent_record.create_or_update_agent_mef_viaf(
                        data=agent_record,
                        dbcommit=True,
                        reindex=True,
                        online=online
                    )
                if viaf_record:
                    viaf_pid = viaf_record.pid
                else:
                    viaf_pid = 'Non'
                mef_actions.append(
                    f'{pid_type}: {agent_record.pid} '
                    f'mef: {mef_record.pid} {mef_action.value} '
                    f'viaf: {viaf_pid}')
                AgentMefRecord.update_indexes()
        return result, '; '.join(mef_actions)

    def get_agents_records(self):
        """Get agents."""
        agents_record = {}
        for agent, agent_data in get_agents_endpoints().items():
            record_class = obj_or_import_string(agent_data.get('record_class'))
            if record_class.viaf_pid_name in self:
                pid = self.get(record_class.viaf_pid_name)
                agent_record = record_class.get_record_by_pid(pid)
                if agent_record:
                    agents_record[agent] = agent_record
        return agents_record

    @classmethod
    def get_missing_agent_pids(cls, agent, verbose=False):
        """Get all missing pids defined in VIAF.

        :param agent: Agent to search for missing pids.
        :param verbose: Verbose.
        :returns: Agent pids without VIAF, VIAF pids without agent
        """
        pids_db = {}
        pids_viaf = []
        record_class = get_entity_class(agent)
        if verbose:
            click.echo(f'Get pids from {agent} ...')
        progress = progressbar(
            items=record_class.get_all_pids(),
            length=record_class.count(),
            verbose=verbose
        )
        for pid in progress:
            pids_db[pid] = 1
        agent_pid_name = f'{record_class.name}_pid'
        if verbose:
            click.echo(f'Get pids from VIAF with {agent_pid_name} ...')
        query = AgentViafSearch() \
            .filter('bool', should=[Q('exists', field=agent_pid_name)]) \
            .source(['pid', agent_pid_name])
        progress = progressbar(
            items=query.scan(),
            length=query.count(),
            verbose=verbose
        )
        for hit in progress:
            viaf_pid = hit.pid
            agent_pid = hit.to_dict().get(agent_pid_name)
            if pids_db.get(agent_pid):
                pids_db.pop(agent_pid)
            else:
                pids_viaf.append(viaf_pid)
        pids_db = [v for v in pids_db]
        return pids_db, pids_viaf


class AgentViafIndexer(ReroIndexer):
    """ViafIndexer."""

    record_cls = AgentViafRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, op_type='index', doc_type='viaf')
