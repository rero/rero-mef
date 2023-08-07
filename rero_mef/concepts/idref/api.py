# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2022 RERO
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

"""API for manipulating IdRef agent."""

from invenio_search.api import RecordsSearch

from .fetchers import idref_id_fetcher
from .minters import idref_id_minter
from .models import ConceptIdrefMetadata
from .providers import ConceptIdrefProvider
from ..api import ConceptIndexer, ConceptRecord


class ConceptIdrefSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'concepts_idref'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class ConceptIdrefRecord(ConceptRecord):
    """Concepts Authority class."""

    minter = idref_id_minter
    fetcher = idref_id_fetcher
    provider = ConceptIdrefProvider
    name = 'idref'
    viaf_source_code = 'RAMEAU'
    pid_type = 'concept_idref_pid'
    model_cls = ConceptIdrefMetadata
    search = ConceptIdrefSearch

    @classmethod
    def get_online_record(cls, id, debug=False):
        """Get online Record.

        Has to be overloaded in agent class.
        """
        from .tasks import idref_get_record
        return idref_get_record(id=id, debug=debug)


class ConceptIdrefIndexer(ConceptIndexer):
    """Concept IDREF indexer."""

    record_cls = ConceptIdrefRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(
            record_id_iterator,
            index=ConceptIdrefSearch.Meta.index,
            doc_type='cidref'
        )
