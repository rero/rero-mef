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

"""API for manipulating mef records."""

from datetime import datetime

import click
import pytz
from elasticsearch_dsl import Q
from flask import current_app
from invenio_search import current_search
from invenio_search.api import RecordsSearch

from .fetchers import mef_id_fetcher
from .minters import mef_id_minter
from .models import MefMetadata
from .providers import MefProvider
from ..api import Action, ReroMefIndexer, ReroMefRecord
from ..utils import get_agent_class, get_agent_classes, progressbar


class MefSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'mef'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class MefRecord(ReroMefRecord):
    """Mef Authority class."""

    minter = mef_id_minter
    fetcher = mef_id_fetcher
    provider = MefProvider
    model_cls = MefMetadata

    @classmethod
    def build_ref_string(cls, agent_pid, agent):
        """Build url for agent's api."""
        with current_app.app_context():
            ref_string = '{url}/api/{agent}/{pid}'.format(
                url=current_app.config.get('RERO_MEF_APP_BASE_URL'),
                agent=agent,
                pid=agent_pid
            )
            return ref_string

    @classmethod
    def get_mef_by_agent_pid(cls, agent_pid, agent_name, pid_only=False):
        """Get mef record by agent pid value."""
        key = '{agent_name}.pid'.format(agent_name=agent_name)
        search = MefSearch() \
            .filter('term', **{key: agent_pid}) \
            .source(['pid'])
        if search.count() > 1:
            current_app.logger.error(
                'MULTIPLE MEF FOUND FOR: {agent} {pid}'.format(
                    agent_name=agent_name,
                    agent_pid=agent_pid
                )
            )
        try:
            mef_pid = next(search.scan()).pid
            if pid_only:
                return mef_pid
            else:
                return cls.get_record_by_pid(mef_pid)
        except StopIteration:
            return None

    @classmethod
    def get_all_mef_pids_by_agent(cls, agent):
        """Get all mef pids for agent."""
        key = '{agent}{identifier}'.format(
            agent=agent, identifier='.pid')
        search = MefSearch()
        results = search.filter(
            'exists',
            field=key
        ).source(['pid', key]).scan()
        for result in results:
            result_dict = result.to_dict()
            yield result_dict.get(agent, {}).get('pid'),\
                result_dict.get('pid')

    @classmethod
    def get_mef_by_viaf_pid(cls, viaf_pid):
        """Get mef record by agent pid value."""
        search = MefSearch()
        result = search.filter(
            'term', viaf_pid=viaf_pid).source(['pid']).scan()
        try:
            mef_pid = next(result).pid
            return cls.get_record_by_pid(mef_pid)
        except StopIteration:
            return None

    @classmethod
    def get_all_pids_without_agents_viaf(cls):
        """Get all pids for records without agents and viaf pids."""
        query = MefSearch()\
            .filter('bool', must_not=[Q('exists', field="viaf_pid")]) \
            .filter('bool', must_not=[Q('exists', field="gnd")]) \
            .filter('bool', must_not=[Q('exists', field="idref")]) \
            .filter('bool', must_not=[Q('exists', field="rero")]) \
            .source('pid')\
            .scan()
        for hit in query:
            yield hit.pid

    @classmethod
    def get_all_pids_without_viaf(cls):
        """Get all pids for records without viaf pid."""
        query = MefSearch()\
            .filter('bool', must_not=[Q('exists', field="viaf_pid")])\
            .filter('bool', should=[Q('exists', field="gnd")]) \
            .filter('bool', should=[Q('exists', field="idref")]) \
            .filter('bool', should=[Q('exists', field="rero")]) \
            .source('pid')\
            .scan()
        for hit in query:
            yield hit.pid

    @classmethod
    def get_agent_pids_with_multiple_mef(
        cls,
        agents=['aggnd', 'aidref', 'agrero'],
        verbose=False
    ):
        """Get agent pids with multiple mef records."""
        pids = {}
        multiple_pids = {}
        missing_pids = {}
        for agent in agents:
            if verbose:
                click.echo('Calculating {agent}:'.format(agent=agent))
            pids[agent] = {}
            multiple_pids[agent] = {}
            missing_pids[agent] = []

            agent_class = get_agent_class(agent)
            agent_name = agent_class.name
            search = MefSearch().filter('exists', field=agent_name)
            progress = progressbar(
                items=search.scan(),
                length=search.count(),
                verbose=verbose
            )
            for hit in progress:
                data = hit.to_dict()
                mef_pid = data['pid']
                agent_pid = data[agent_name]['pid']
                pids[agent].setdefault(agent_pid, [])
                pids[agent][agent_pid].append(mef_pid)
                if len(pids[agent][agent_pid]) > 1:
                    multiple_pids[agent][agent_pid] = pids[agent][agent_pid]
            if len(pids[agent]) < agent_class.count():
                progress = progressbar(
                    items=agent_class.get_all_pids(),
                    length=agent_class.count(),
                    verbose=verbose
                )
                for pid in progress:
                    if not pids[agent].pop(pid, None):
                        missing_pids[agent].append(pid)
            else:
                pids[agent] = {}
        return pids, multiple_pids, missing_pids

        # multiple_pids = {}
        # for agent in agents:
        #     multiple_pids[agent] = {}
        #     agent_class = get_agent_class(agent)
        #     if agent_class:
        #         agent_name = agent_class.name
        #         search = MefSearch()
        #         search.aggs.bucket(
        #             'MULTIPLE',
        #             'terms',
        #             field='{agent}.pid'.format(agent=agent_name),
        #             min_doc_count=2,
        #             size=size
        #         )
        #         res = search.execute()
        #         for values in res.aggregations.MULTIPLE.buckets:
        #             agent_pid = values.key
        #             field = '{agent}.pid'.format(agent=agent_name)
        #             search = MefSearch().filter(
        #                 Q('term', **{field: agent_pid}))
        #             mef_pids = []
        #             for hit in search:
        #                 mef_pids.append(hit.pid)
        #             mef_pids = sorted(mef_pids)
        #             multiple_pids[agent][agent_pid] = mef_pids
        # return multiple_pids

    @classmethod
    def get_all_missing_agents_pids(
        cls,
        agents=['aggnd', 'aidref', 'agrero'],
        verbose=False
    ):
        """Get all missing agents."""
        missing_pids = {}
        to_much_pids = {}
        used_classes = {}
        agent_classes = get_agent_classes()
        for agent_classe in agent_classes:
            if agent_classe in agents:
                used_classes[agent_classe] = agent_classes[agent_classe]
        for agent, agent_class in used_classes.items():
            if verbose:
                click.echo(
                    'Get pids from {agent} ...'.format(agent=agent)
                )
            missing_pids[agent] = {}
            progress = progressbar(
                items=agent_class.get_all_pids(),
                length=agent_class.count(),
                verbose=verbose
            )
            for pid in progress:
                missing_pids[agent][pid] = 1
        if verbose:
            click.echo('Get pids from mef and calculate missing ...')
        progress = progressbar(
            items=MefSearch().filter('match_all').source().scan(),
            length=MefSearch().filter('match_all').source().count(),
            verbose=verbose
        )
        for hit in progress:
            pid = hit.pid
            data = hit.to_dict()
            for agent, agent_class in used_classes.items():
                agent_data = data.get(agent_class.name)
                if agent_data:
                    agent_pid = agent_data.get('pid')
                    if not missing_pids[agent].pop(agent_pid, None):
                        to_much_pids.setdefault(pid, {})
                        to_much_pids[pid][agent] = agent_pid
        return missing_pids, to_much_pids

    @classmethod
    def get_all_missing_viaf_pids(cls, verbose=False):
        """Get all missing viaf pids."""
        from ..viaf.api import ViafRecord
        missing_pids = {}
        if verbose:
            click.echo('Get pids from viaf ...')
        progress = progressbar(
            items=ViafRecord.get_all_pids(),
            length=ViafRecord.count(),
            verbose=verbose
        )
        for pid in progress:
            missing_pids[pid] = 1
        if verbose:
            click.echo('Get pids from mef and calculate missing ...')
        progress = progressbar(
            items=MefSearch().filter('match_all').source().scan(),
            length=MefSearch().filter('match_all').source().count(),
            verbose=True
        )
        for hit in progress:
            data = hit.to_dict()
            viaf_pid = data.get('viaf_pid')
            if viaf_pid:
                missing_pids.pop(viaf_pid, None)
        return missing_pids

    def mark_as_deleted(self, dbcommit=False, reindex=False):
        """Mark record as deleted."""
        # if current_app.config['INDEXER_REPLACE_REFS']:
        #     data = deepcopy(self.replace_refs())
        # else:
        #     data = self.dumps()
        # data['_deleted'] = pytz.utc.localize(self.created).isoformat()
        #
        # indexer = MefIndexer()
        # index, doc_type = indexer.record_to_index(self)
        # print('---->', index, doc_type)
        # body = indexer._prepare_record(data, index, doc_type)
        # index, doc_type = indexer._prepare_index(index, doc_type)
        # print('---->', index, doc_type)
        #
        # return indexer.client.index(
        #     id=str(self.id),
        #     version=self.revision_id,
        #     version_type=indexer._version_type,
        #     index=index,
        #     doc_type=doc_type,
        #     body=body
        # )
        self['deleted'] = pytz.utc.localize(datetime.now()).isoformat()
        self.update(data=self, dbcommit=dbcommit, reindex=reindex)
        return self

    @classmethod
    def create_deleted(cls, agent, dbcommit=False, reindex=False):
        """Create a deleted record for an agent."""
        data = {}
        data[agent.name] = {'$ref': cls.build_ref_string(
            agent_pid=agent.pid,
            agent=agent.name
        )}
        data['deleted'] = pytz.utc.localize(datetime.now()).isoformat()
        return cls.create(data=data, dbcommit=dbcommit, reindex=reindex)

    @classmethod
    def update_indexes(cls):
        """Update indexes."""
        try:
            current_search.flush_and_refresh(index='mef')
        except Exception as err:
            current_app.logger.error(
                'ERROR flush and refresh: {err}'.format(err=err)
            )

    def delete_agent(self, agent_record, dbcommit=False, reindex=False):
        """Delete Agency from record."""
        action = Action.DISCARD
        if self.pop(agent_record.agent, None):
            action = Action.UPDATE
            self.replace(
                data=self,
                dbcommit=dbcommit,
                reindex=reindex
            )
            if reindex:
                MefRecord.update_indexes()
        return self, action


class MefIndexer(ReroMefIndexer):
    """MefIndexer."""

    record_cls = MefRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, op_type='index', doc_type='mef')
