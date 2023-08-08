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

from copy import deepcopy

from flask import current_app
from invenio_search.api import RecordsSearch

from .fetchers import mef_id_fetcher
from .minters import mef_id_minter
from .models import ConceptMefMetadata
from .providers import ConceptMefProvider
from ..utils import get_concept_classes
from ...api import ReroIndexer
from ...api_mef import EntityMefRecord


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
    name = 'mef'
    model_cls = ConceptMefMetadata
    search = ConceptMefSearch
    mef_type = 'CONCEPTS'
    entities = ['idref', 'rero']

    @classmethod
    def create(cls, data, id_=None, delete_pid=False, dbcommit=False,
               reindex=False, md5=True, **kwargs):
        """Create a new agent record."""
        data['type'] = 'bf:Topic'
        concept_classes = get_concept_classes()
        for concept in cls.entities:
            if concept := data.get(concept):
                ref_split = concept['$ref'].split('/')
                ref_type = ref_split[-2]
                ref_pid = ref_split[-1]
                for _, concept_class in concept_classes.items():
                    if concept_class.name == ref_type:
                        if concept_rec := concept_class.get_record_by_pid(
                            ref_pid
                        ):
                            data['type'] = concept_rec['type']
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
        data['sources'] = [
            concept for concept in self.entities if data.get(concept)]
        return data

    def add_information(self, resolve=False, sources=False):
        """Add information to record.

        Sources will be also added if resolve is True.
        :param resolve: resolve $refs
        :param sources: Add sources information to record
        :returns: record
        """
        replace_refs_data = ConceptMefRecord(deepcopy(self).replace_refs())
        data = replace_refs_data if resolve else deepcopy(self)
        my_sources = []
        for concept in self.entities:
            if concept_data := data.get(concept):
                # we got a error status in data
                if concept_data.get('status'):
                    data.pop(concept)
                    current_app.logger.error(
                        f'MEF replace refs {data.get("pid")} {concept}'
                        f' status: {concept_data.get("status")}'
                        f' {concept_data.get("message")}')
                else:
                    my_sources.append(concept)
                for concept in self.entities:
                    if metadata := replace_refs_data.get(
                            concept, {}).get('metadata'):
                        data[concept] = metadata
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
        search = ConceptMefSearch().filter({'term': {f'{pid_type}.pid': pid}})
        if search.count() > 0:
            data = next(search.scan()).to_dict()
            new_pid = None
            if relation_pid := data.get(pid_type, {}).get('relation_pid'):
                if relation_pid['type'] == 'redirect_to':
                    new_pid = relation_pid['value']
            elif pid_type == 'idref':
                # Find new pid from redirect_pid redirect_from
                search = ConceptMefSearch() \
                        .filter('term', idref__relation_pid__value=pid)
                if search.count() > 0:
                    new_data = next(search.scan()).to_dict()
                    new_pid = new_data.get('idref', {}).get('pid')
            return cls.get_latest(pid_type=pid_type, pid=new_pid) \
                if new_pid else data
        return {}


class ConceptMefIndexer(ReroIndexer):
    """Concept MEF indexer."""

    record_cls = ConceptMefRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(
            record_id_iterator,
            index=ConceptMefSearch.Meta.index,
            doc_type='comef'
        )
