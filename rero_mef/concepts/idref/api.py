# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating IdRef agent."""

from flask import current_app
from invenio_search.api import RecordsSearch

from rero_mef.api import Association

from ..api import ConceptIndexer, ConceptRecord
from ..utils import bnf_ark_disagreements, bnf_association_identifiers
from .fetchers import idref_id_fetcher
from .minters import idref_id_minter
from .models import ConceptIdrefMetadata
from .providers import ConceptIdrefProvider


class ConceptIdrefSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = "concepts_idref"
        doc_types = None
        fields = ("*",)
        facets = {}

        default_filter = None


class ConceptIdrefRecord(ConceptRecord):
    """Concepts Authority class."""

    minter = idref_id_minter
    fetcher = idref_id_fetcher
    provider = ConceptIdrefProvider
    name = "idref"
    viaf_source_code = "RAMEAU"
    pid_type = "concept_idref_pid"
    model_cls = ConceptIdrefMetadata
    search = ConceptIdrefSearch

    @classmethod
    def get_online_record(cls, id_, debug=False):
        """Get online Record.

        :param id_: Id of online record.
        :param debug: Debug print.
        :returns: record or None
        """
        from .tasks import idref_get_record

        return idref_get_record(id_=id_, debug=debug)

    @property
    def association(self):
        """Get the BNF association identifiers from identifiedBy.

        A RAMEAU heading that absorbed several BNF records keeps every one of their numbers, so all of them are
        stated: a GND record matches when its own number is among them. IdRef states no strength, so the level
        stays None.

        :returns: An :class:`Association` carrying every BNF number the record states.
        """
        identified_by_lists = [self.get("identifiedBy", [])]
        if only_ark := bnf_ark_disagreements(identified_by_lists):
            current_app.logger.warning(
                f"BNF ARK DISAGREES WITH bf:Nbn: {self.name} {self.pid} | ark {', '.join(sorted(only_ark))}"
            )
        return Association(frozenset(bnf_association_identifiers(identified_by_lists)))

    @property
    def association_info(self):
        """Get associated record."""
        from rero_mef.concepts import (
            ConceptGndRecord,
            ConceptGndSearch,
            ConceptMefRecord,
        )

        ConceptGndRecord.flush_indexes()
        return {
            "record": self.get_association_record(
                association_cls=ConceptGndRecord, association_search=ConceptGndSearch
            ),
            "record_cls": ConceptGndRecord,
            "search_cls": ConceptGndSearch,
            "mef_cls": ConceptMefRecord,
        }


class ConceptIdrefIndexer(ConceptIndexer):
    """Concept IDREF indexer."""

    record_cls = ConceptIdrefRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, index=ConceptIdrefSearch.Meta.index, doc_type="cidref")
