# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2021 RERO
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

from datetime import datetime, timezone

from flask import current_app
from invenio_search import current_search
from invenio_search.api import RecordsSearch

from .fetchers import mef_id_fetcher
from .minters import mef_id_minter
from .models import ConceptMefMetadata
from .providers import ConceptMefProvider
from ...api import Action, ReroIndexer
from ...api_mef import EntityMefRecord
from ...utils import mef_get_all_missing_entity_pids


def build_ref_string(concept_pid, concept):
    """Build url for concept's api.

    :param concept_pid: Pid of concept.
    :param concept: Type of concept.
    :returns: Reference string to record.
    """
    with current_app.app_context():
        return (f'{current_app.config.get("RERO_MEF_APP_BASE_URL")}'
                f'/api/concepts/{concept}/{concept_pid}')


class ConceptMefSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'concepts_mef'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class ConceptMefRecord(EntityMefRecord):
    """Mef concept class."""

    minter = mef_id_minter
    fetcher = mef_id_fetcher
    provider = ConceptMefProvider
    model_cls = ConceptMefMetadata
    search = ConceptMefSearch
    mef_type = 'CONCEPTS'
    entities = ['rero']

    @classmethod
    def flush_indexes(cls):
        """Update indexes."""
        try:
            current_search.flush_and_refresh(index='concepts_mef')
        except Exception as err:
            current_app.logger.error(
                'ERROR flush and refresh: {err}'.format(err=err)
            )

    @classmethod
    def get_all_missing_concepts_pids(cls, agent, verbose=False):
        """Get all missing agent pids.

        :param agent: agent name to get the missing pids.
        :param verbose: Verbose.
        :returns: Missing VIAF pids.
        """
        return mef_get_all_missing_entity_pids(mef_class=cls, entity=agent,
                                               verbose=verbose)

    def replace_refs(self):
        """Replace $ref with real data."""
        data = super().replace_refs()
        sources = []
        for agent in ['rero']:
            if agent in data and data[agent]:
                sources.append(agent)
                if metadata := data[agent].get('metadata'):
                    data[agent] = metadata
        data['sources'] = sources
        return data

    def create_or_update_mef_viaf_record(self, dbcommit=False, reindex=False,
                                         online=False):
        """Create or update MEF and VIAF record.

        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :param online: Try to get VIAF record online.
        :returns: MEF record, MEF action, VIAF record, VIAF
        """
        return self, Action.Error, None, False

    @classmethod
    def create_deleted(cls, record, dbcommit=False, reindex=False):
        """Create a deleted record for an record.

        :param record: Record to create.
        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :returns: Created record.
        """
        data = {
            record.name: {'$ref': build_ref_string(record.pid, record.name)},
            'deleted': datetime.now(timezone.utc).isoformat()
        }
        return cls.create(data=data, dbcommit=dbcommit, reindex=reindex)


class ConceptMefIndexer(ReroIndexer):
    """MefIndexer."""

    record_cls = ConceptMefRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, op_type='index', doc_type='mef')
