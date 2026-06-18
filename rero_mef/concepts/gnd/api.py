# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating Gnd agent."""

from flask import current_app
from invenio_search.api import RecordsSearch

from ..api import ConceptIndexer, ConceptRecord
from .fetchers import gnd_id_fetcher
from .minters import gnd_id_minter
from .models import ConceptGndMetadata
from .providers import ConceptGndProvider


class ConceptGndSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = "concepts_gnd"
        doc_types = None
        fields = ("*",)
        facets = {}

        default_filter = None


class ConceptGndRecord(ConceptRecord):
    """Concepts Authority class."""

    minter = gnd_id_minter
    fetcher = gnd_id_fetcher
    provider = ConceptGndProvider
    name = "gnd"
    viaf_source_code = "RAMEAU"
    pid_type = "concept_gnd_pid"
    model_cls = ConceptGndMetadata
    search = ConceptGndSearch

    @classmethod
    def get_online_record(cls, id_, debug=False):
        """Get online Record.

        :param id_: Id of online record.
        :param debug: Debug print.
        :returns: record or None
        """
        from .tasks import gnd_get_record

        return gnd_get_record(id_=id_, debug=debug)

    @property
    def association_identifier(self):
        """Get associated identifier."""
        for match_type, max_count in current_app.config.get(
            "RERO_MEF_CONCEPTS_GND_MATCHES", {}
        ).items():
            matches = self.get(match_type, [])
            match_count = 0
            match_value = ""
            for match in matches:
                for identified_by in match.get("identifiedBy", []):
                    if (
                        identified_by.get("source") == "BNF"
                        and identified_by.get("type") == "bf:Nbn"
                        and identified_by.get("value", "").startswith("FRBNF")
                    ):
                        match_count += 1
                        match_value = identified_by.get("value")
            if match_value and match_count <= max_count:
                return match_value[:13]
        return None

    def get_association_record(self, association_cls, association_search):
        """Get associated record.

        :params association_cls: Association class
        :params association_search: Association search class.
        :returns: Associated record.
        """
        if association_identifier := self.association_identifier:
            # Test if my identifier is unique
            exact_count = (
                self.search()
                .filter("term", exactMatch__identifiedBy__source="BNF")
                .filter("term", exactMatch__identifiedBy__type="bf:Nbn")
                .filter("term", exactMatch__identifiedBy__value=association_identifier)
                .count()
            )
            if exact_count != 1:
                # we have 0 or multiple exact matches
                count = (
                    self.search()
                    .filter("term", _association_identifier=association_identifier)
                    .count()
                )
                if count > 1:
                    current_app.logger.error(
                        f"MULTIPLE IDENTIFIERS FOUND FOR: {self.name} {self.pid} "
                        f"| {association_identifier}"
                    )
                    return None
            # Get associated record
            query = association_search().filter(
                "term", _association_identifier=association_identifier
            )
            if query.count() > 1:
                current_app.logger.error(
                    f"MULTIPLE ASSOCIATIONS IDENTIFIERS FOUND FOR: {self.name} {self.pid} "
                    f"| {association_identifier}"
                )
            elif query.count() == 1:
                hit = next(query.source("pid").scan())
                return association_cls.get_record_by_pid(hit.pid)
        return None

    @property
    def association_info(self):
        """Get associated record."""
        from rero_mef.concepts import (
            ConceptIdrefRecord,
            ConceptIdrefSearch,
            ConceptMefRecord,
        )

        ConceptIdrefRecord.flush_indexes()
        return {
            "identifier": self.association_identifier,
            "record": self.get_association_record(
                association_cls=ConceptIdrefRecord,
                association_search=ConceptIdrefSearch,
            ),
            "record_cls": ConceptIdrefRecord,
            "search_cls": ConceptIdrefSearch,
            "mef_cls": ConceptMefRecord,
        }


class ConceptGndIndexer(ConceptIndexer):
    """Concept GND indexer."""

    record_cls = ConceptGndRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(
            record_id_iterator, index=ConceptGndSearch.Meta.index, doc_type="cognd"
        )
