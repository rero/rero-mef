# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating Gnd agent."""

from flask import current_app
from invenio_search.api import RecordsSearch

from rero_mef.api import Association

from ..api import ConceptIndexer, ConceptRecord
from ..utils import (
    MATCH_TYPES,
    bnf_ark_disagreements_by_match_type,
    bnf_association_identifiers,
)
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

    def _warn_about_arks(self):
        """Warn when the BNF ark uris of a match type state a number its `bf:Nbn` values do not.

        Every match type is audited, not only the one the association is read from: a contradiction in a block the
        selection never reaches is still a source data error to fix in GND.
        """
        for match_type, only_ark in bnf_ark_disagreements_by_match_type(self).items():
            current_app.logger.warning(
                f"BNF ARK DISAGREES WITH bf:Nbn: {self.name} {self.pid} | "
                f"{match_type} ark {', '.join(sorted(only_ark))}"
            )

    @property
    def association(self):
        """Get the BNF association identifier and the match type it comes from.

        `exactMatch` asserts equivalence and wins over `closeMatch`, which only asserts relatedness, so the first
        block type carrying a BNF number decides. A record naming several different numbers states no usable
        identifier at all.

        :returns: An :class:`Association` carrying the BNF number and the match type it was read from.
        """
        self._warn_about_arks()
        for match_type in MATCH_TYPES:
            matches = self.get(match_type, [])
            if identifiers := bnf_association_identifiers(match.get("identifiedBy", []) for match in matches):
                if len(identifiers) > 1:
                    current_app.logger.info(
                        f"MULTIPLE ASSOCIATIONS FOUND FOR: {self.name} {self.pid} | "
                        f"{match_type} {', '.join(sorted(identifiers))}"
                    )
                    return Association()
                return Association(frozenset(identifiers), match_type)
        return Association()

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
        super().bulk_index(record_id_iterator, index=ConceptGndSearch.Meta.index, doc_type="cognd")
