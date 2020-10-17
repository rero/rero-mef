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

"""API for manipulating contributions."""

from datetime import datetime

import click
import pytz
from elasticsearch_dsl import Q
from flask import current_app
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records_rest.utils import obj_or_import_string
from invenio_search import current_search
from invenio_search.api import RecordsSearch

from .fetchers import mef_id_fetcher
from .minters import mef_id_minter
from .models import MefMetadata
from .providers import MefProvider
from ..api import Action, ContributionIndexer, ContributionRecord
from ..utils import get_agent_classes, get_agents_endpoints, progressbar


class MefSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'mef'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class MefRecord(ContributionRecord):
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
    def get_mef_by_agent_pid(cls, agent_pid, agent, pid_only=False):
        """Get mef record by agent pid value."""
        key = '{agent}.pid'.format(agent=agent)
        result = MefSearch().query(
            'match', **{key: agent_pid}).source(['pid']).scan()
        try:
            mef_pid = next(result).pid
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
    def mef_data_from_viaf(cls, mef_data, viaf_record):
        """Create Mef data from Viaf."""
        has_refs = False
        if not mef_data:
            mef_data = {}
        if viaf_record and viaf_record.get('pid'):
            mef_data['viaf_pid'] = viaf_record.get('pid')
        for agent, agent_data in get_agents_endpoints().items():
            mef_data.pop(agent, None)
            pid_name = '{agent}_pid'.format(agent=agent)
            pid_value = viaf_record.get(pid_name)
            if pid_value:
                agent_class = obj_or_import_string(
                    agent_data.get('record_class')
                )
                try:
                    record = agent_class.get_record_by_pid(pid_value)
                    if record and not record.get('deleted'):
                        ref_string = cls.build_ref_string(
                            agent=agent, agent_pid=pid_value
                        )
                        mef_data[agent] = {'$ref': ref_string}
                        has_refs = True
                except PIDDoesNotExistError:
                    pass
        return mef_data, has_refs

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
    def get_all_missing_agents_pids(
            cls,
            agents=['gnd', 'idref', 'rero'],
            verbose=False
    ):
        """Get all missing agents."""
        missing_pids = {}
        agent_classes = get_agent_classes()
        used_classes = {}
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
        # progress = progressbar(
        #     items=cls.get_all_ids(),
        #     length=cls.count(),
        #     verbose=verbose
        # )
        # for id in progress:
        #     mef_record = cls.get_record_by_id(id)
        #     for agent in used_classes:
        #         agent_ref = mef_record.get(agent, {}).get('$ref', '')
        #         agent_pid = agent_ref.split('/')[-1]
        #         missing_pids[agent].pop(agent_pid, None)

        # working with ES is much faster
        progress = progressbar(
            items=MefSearch().filter('match_all').source().scan(),
            length=MefSearch().filter('match_all').source().count(),
            verbose=True
        )
        for hit in progress:
            pid = hit.pid
            data = hit.to_dict()
            for agent in used_classes:
                agent_data = data.get(agent)
                if agent_data:
                    missing_pids[agent].pop(agent_data.get('pid'), None)
        return missing_pids

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
    def update_indexes(cls):
        """Update indexes."""
        current_search.flush_and_refresh(index='mef-mef-contribution-v0.0.1')

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


class MefIndexer(ContributionIndexer):
    """MefIndexer."""

    record_cls = MefRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, op_type='index', doc_type='mef')
