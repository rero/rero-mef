# -*- coding: utf-8 -*-
#
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
            "RERO_MEF_PLACES_GND_MATCHES", {}
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
