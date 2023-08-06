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

"""API for manipulating MEF records."""

from copy import deepcopy

import click
from flask import current_app
from invenio_search.api import RecordsSearch

from .fetchers import mef_id_fetcher
from .minters import mef_id_minter
from .models import AgentMefMetadata
from .providers import MefProvider
from ...api import ReroIndexer
from ...api_mef import EntityMefRecord
from ...utils import get_entity_classes, progressbar


def build_ref_string(agent_pid, agent):
    """Build url for agent's api.

    :param agent_pid: Agent pid.
    :param agent: Agent type.
    :returns: URL to agent
    """
    with current_app.app_context():
        return (f'{current_app.config.get("RERO_MEF_APP_BASE_URL")}'
                f'/api/agents/{agent}/{agent_pid}')


class AgentMefSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'mef'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class AgentMefRecord(EntityMefRecord):
    """Mef agent class."""

    minter = mef_id_minter
    fetcher = mef_id_fetcher
    provider = MefProvider
    name = 'mef'
    model_cls = AgentMefMetadata
    search = AgentMefSearch
    mef_type = 'AGENTS'
    entities = ['idref', 'gnd', 'rero']

    @classmethod
    def get_all_missing_viaf_pids(cls, verbose=False):
        """Get all missing VIAF pids.

        :param verbose: Verbose.
        :returns: Missing VIAF pids.
        """
        from ..viaf.api import AgentViafRecord
        if verbose:
            click.echo('Get pids from VIAF ...')
        progress = progressbar(
            items=AgentViafRecord.get_all_pids(),
            length=AgentViafRecord.count(),
            verbose=verbose
        )
        missing_pids = {pid: 1 for pid in progress}
        if verbose:
            click.echo('Get pids from MEF and calculate missing ...')
        query = cls.search().filter('exists', field='viaf_pid')
        progress = progressbar(
            items=query.source(['pid', 'viaf_pid']).scan(),
            length=query.count(),
            verbose=True
        )
        non_existing_pids = {hit.pid: hit.viaf_pid for hit in progress
                             if not missing_pids.pop(hit.viaf_pid, None)}

        return list(missing_pids), non_existing_pids

    @classmethod
    def create(cls, data, id_=None, delete_pid=False, dbcommit=False,
               reindex=False, md5=True, **kwargs):
        """Create a new agent record."""
        # replace_refs_data = deepcopy(data).replace_refs()
        data['type'] = 'bf:Person'
        entity_classes = get_entity_classes()
        for agent in cls.entities:
            if agent := data.get(agent):
                ref_split = agent['$ref'].split('/')
                ref_type = ref_split[-2]
                ref_pid = ref_split[-1]
                for _, entity_class in entity_classes.items():
                    if entity_class.name == ref_type:
                        if entity_rec := entity_class.get_record_by_pid(
                            ref_pid
                        ):
                            data['type'] = entity_rec['type']
                            break

        return super().create(
            data=data,
            id_=id_,
            delete_pid=delete_pid,
            dbcommit=dbcommit,
            reindex=reindex,
            md5=False,
            **kwargs
        )

    def replace_refs(self):
        """Replace $ref with real data."""
        data = deepcopy(self)
        data = super().replace_refs()
        sources = [agent for agent in self.entities if data.get(agent)]
        data['sources'] = sources
        return data

    def add_information(self, resolve=False, sources=False):
        """Add information to record.

        Sources will be also added if resolve is True.
        :param resolve: resolve $refs
        :param sources: Add sources information to record
        :returns: record
        """
        replace_refs_data = AgentMefRecord(deepcopy(self).replace_refs())
        data = replace_refs_data if resolve else deepcopy(self)
        my_sources = []
        for agent in self.entities:
            if agent_data := data.get(agent):
                # we got a error status in data
                if agent_data.get('status'):
                    data.pop(agent)
                    current_app.logger.error(
                        f'MEF replace refs {data.get("pid")} {agent}'
                        f' status: {agent_data.get("status")}'
                        f' {agent_data.get("message")}')
                else:
                    my_sources.append(agent)
                for agent in self.entities:
                    if agent_data := replace_refs_data.get(agent):
                        if metadata := replace_refs_data[agent] \
                                .get('metadata'):
                            data[agent] = metadata
        if my_sources and (resolve or sources):
            data['sources'] = my_sources
        return data

    @classmethod
    def get_latest(cls, pid_type, pid):
        """Get latest Mef record for pid_type and pid.

        :param pid_type: pid type to use.
        :param pid: pid to use..
        :returns: latest record.
        """
        search = AgentMefSearch().filter({'term': {f'{pid_type}.pid': pid}})
        if search.count() > 0:
            data = next(search.scan()).to_dict()
            new_pid = None
            if relation_pid := data.get(pid_type, {}).get('relation_pid'):
                if relation_pid['type'] == 'redirect_to':
                    new_pid = relation_pid['value']
            elif pid_type == 'idref':
                # Find new pid from redirect_pid redirect_from
                search = AgentMefSearch() \
                        .filter('term', idref__relation_pid__value=pid)
                if search.count() > 0:
                    new_data = next(search.scan()).to_dict()
                    new_pid = new_data.get('idref', {}).get('pid')
            for agent in cls.entities:
                if agent_data := data.get(agent):
                    if not agent_data.get('type'):
                        data[agent]['type'] = agent_data['bf:Agent']
                        if not data.get('type'):
                            data['type'] = agent_data['bf:Agent']
            return cls.get_latest(pid_type=pid_type, pid=new_pid) \
                if new_pid else data
        return {}


class AgentMefIndexer(ReroIndexer):
    """Agent MEF indexer."""

    record_cls = AgentMefRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(
            record_id_iterator,
            index=AgentMefSearch.Meta.index,
            doc_type='mef'
        )
