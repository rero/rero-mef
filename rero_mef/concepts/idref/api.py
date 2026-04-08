# RERO MEF
# Copyright (C) 2024 RERO
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

from flask import current_app
from invenio_search.api import RecordsSearch

from ..api import ConceptIndexer, ConceptRecord
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

    def get_association_record(self, association_cls, association_search):
        """Get associated record.

        :params association_cls: Association class
        :params association_search: Association search class.
        :returns: Associated record.
        """
        if association_identifier := self.association_identifier:
            # Test if my identifier is unique
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
            associated_count = query.count()
            if associated_count > 1:
                # GND sometimes has multiple records sharing the same BNF identifier.
                # Disambiguate by requiring exactly one GND record with an exact BNF match.
                exact_pids = list(
                    dict.fromkeys(
                        hit.pid
                        for hit in query.source(["pid", "exactMatch"]).scan()
                        for exact_match in hit.to_dict().get("exactMatch", [])
                        for identified_by in exact_match.get("identifiedBy", [])
                        if identified_by.get("source") == "BNF"
                        and identified_by.get("type") == "bf:Nbn"
                        and identified_by.get("value") == association_identifier
                    )
                )
                if len(exact_pids) == 1:
                    return association_cls.get_record_by_pid(exact_pids[0])
                current_app.logger.error(
                    f"MULTIPLE ASSOCIATIONS IDENTIFIERS FOUND FOR: {self.name} {self.pid} "
                    f"| {association_identifier}"
                )
            elif associated_count == 1:
                hit = next(query.source("pid").scan())
                return association_cls.get_record_by_pid(hit.pid)
        return None

    @property
    def association_identifier(self):
        """Get associated identifier from identifiedBy."""
        if pids := [
            identified_by.get("value")
            for identified_by in self.get("identifiedBy", [])
            if identified_by.get("source") == "BNF"
            and identified_by.get("value", "").startswith("FRBNF")
        ]:
            if len(pids) > 1:
                current_app.logger.error(
                    f"MULTIPLE ASSOCIATIONS FOUND FOR: {self.name} {self.pid} | {', '.join(pids)}"
                )
            if pids:
                return pids[-1]
        return None

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
            "identifier": self.association_identifier,
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
        super().bulk_index(
            record_id_iterator, index=ConceptIdrefSearch.Meta.index, doc_type="cidref"
        )
