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

"""API for manipulating RERO agent."""

from invenio_search.api import RecordsSearch

from .fetchers import rero_id_fetcher
from .minters import rero_id_minter
from .models import ConceptReroMetadata
from .providers import ConceptReroProvider
from ..api import ConceptIndexer, ConceptRecord


class ConceptReroSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'concepts_rero'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class ConceptReroRecord(ConceptRecord):
    """Concepts Authority class."""

    minter = rero_id_minter
    fetcher = rero_id_fetcher
    provider = ConceptReroProvider
    viaf_source_code = 'RAMEAU'
    pid_type = 'concept_rero_pid'
    model_cls = ConceptReroMetadata
    name = 'rero'

    # @classmethod
    # def get_online_record(cls, id, verbose=False):
    #     """Get online record."""
    #     from .tasks import concepts_get_record
    #     return concepts_get_record(id=id, verbose=verbose)

    def reindex(self, forceindex=False):
        """Reindex record."""
        if forceindex:
            result = ConceptReroIndexer(version_type='external_gte').index(self)
        else:
            result = ConceptReroIndexer().index(self)
        return result


class ConceptReroIndexer(ConceptIndexer):
    """ConceptsIndexer."""

    record_cls = ConceptReroRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, op_type='index', doc_type='corero')
