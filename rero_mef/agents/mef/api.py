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

import click
from elasticsearch_dsl import Q
from flask import current_app
from invenio_search import current_search
from invenio_search.api import RecordsSearch

from .fetchers import mef_id_fetcher
from .minters import mef_id_minter
from .models import AgentMefMetadata
from .providers import MefProvider
from ...api import ReroIndexer
from ...api_mef import EntityMefRecord
from ...utils import progressbar


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
    model_cls = AgentMefMetadata
    search = AgentMefSearch
    mef_type = 'AGENTS'

    @classmethod
    def build_ref_string(cls, agent_pid, agent):
        """Build url for agent's api.

        :param agent_pid: Agent pid.
        :param agent: Agent type.
        :returns: URL to agent
        """
        with current_app.app_context():
            ref_string = (f'{current_app.config.get("RERO_MEF_APP_BASE_URL")}'
                          f'/api/agents/{agent}/{agent_pid}')
            return ref_string

    @classmethod
    def update_indexes(cls):
        """Update indexes."""
        try:
            current_search.flush_and_refresh(index='mef')
        except Exception as err:
            current_app.logger.error(f'ERROR flush and refresh: {err}')

    @classmethod
    def get_all_missing_viaf_pids(cls, verbose=False):
        """Get all missing VIAF pids.

        :param verbose: Verbose.
        :returns: Missing VIAF pids.
        """
        from ..viaf.api import AgentViafRecord
        missing_pids = {}
        if verbose:
            click.echo('Get pids from VIAF ...')
        progress = progressbar(
            items=AgentViafRecord.get_all_pids(),
            length=AgentViafRecord.count(),
            verbose=verbose
        )
        for pid in progress:
            missing_pids[pid] = 1
        if verbose:
            click.echo('Get pids from MEF and calculate missing ...')
        progress = progressbar(
            items=cls.search().filter('match_all').source().scan(),
            length=cls.search().filter('match_all').source().count(),
            verbose=True
        )
        for hit in progress:
            data = hit.to_dict()
            viaf_pid = data.get('viaf_pid')
            if viaf_pid:
                missing_pids.pop(viaf_pid, None)
        return missing_pids

    def replace_refs(self):
        """Replace $ref with real data."""
        data = super().replace_refs()
        sources = []
        for agent in ['rero', 'gnd', 'idref']:
            if agent in data and data[agent]:
                sources.append(agent)
                metadata = data[agent].get('metadata')
                if metadata:
                    data[agent] = metadata
                    data['type'] = metadata['bf:Agent']
        data['sources'] = sources
        return data

    @classmethod
    def get_all_pids_without_agents_viaf(cls):
        """Get all pids for records without agents and VIAF pids.

        :returns: Generator of MEF pids without agent links and without VIAF.
        """
        query = AgentMefSearch()\
            .filter('bool', must_not=[Q('exists', field="viaf_pid")]) \
            .filter('bool', must_not=[Q('exists', field="gnd")]) \
            .filter('bool', must_not=[Q('exists', field="idref")]) \
            .filter('bool', must_not=[Q('exists', field="rero")]) \
            .source('pid')\
            .scan()
        for hit in query:
            yield hit.pid


class AgentMefIndexer(ReroIndexer):
    """AgentMefIndexer."""

    record_cls = AgentMefRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, op_type='index', doc_type='mef')
