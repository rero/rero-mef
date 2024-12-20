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

from ..api import ConceptIndexer, ConceptRecord
from .fetchers import rero_id_fetcher
from .minters import rero_id_minter
from .models import ConceptReroMetadata
from .providers import ConceptReroProvider


class ConceptReroSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = "concepts_rero"
        doc_types = None
        fields = ("*",)
        facets = {}

        default_filter = None


class ConceptReroRecord(ConceptRecord):
    """Concepts Authority class."""

    minter = rero_id_minter
    fetcher = rero_id_fetcher
    provider = ConceptReroProvider
    name = "rero"
    viaf_source_code = "RAMEAU"
    pid_type = "concept_rero_pid"
    model_cls = ConceptReroMetadata
    search = ConceptReroSearch

    @property
    def association_identifier(self):
        """Get associated identifier from identifiedBy."""

    @property
    def association_info(self):
        """Get associated record."""
        from rero_mef.concepts import ConceptMefRecord

        return {
            "identifier": self.association_identifier,
            "record": None,
            "record_cls": None,
            "search_cls": None,
            "mef_cls": ConceptMefRecord,
        }


class ConceptReroIndexer(ConceptIndexer):
    """Concept RERO indexer."""

    record_cls = ConceptReroRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(
            record_id_iterator, index=ConceptReroSearch.Meta.index, doc_type="corero"
        )
