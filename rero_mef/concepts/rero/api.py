# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

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
