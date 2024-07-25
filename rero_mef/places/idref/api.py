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

"""API for manipulating IdRef agent."""

from flask import current_app
from invenio_search.api import RecordsSearch

from rero_mef.places.api import PlaceIndexer, PlaceRecord

from .fetchers import idref_id_fetcher
from .minters import idref_id_minter
from .models import PlaceIdrefMetadata
from .providers import PlaceIdrefProvider


class PlaceIdrefSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = "places_idref"
        doc_types = None
        fields = ("*",)
        facets = {}

        default_filter = None


class PlaceIdrefRecord(PlaceRecord):
    """Places Authority class."""

    minter = idref_id_minter
    fetcher = idref_id_fetcher
    provider = PlaceIdrefProvider
    name = "idref"
    viaf_source_code = "RAMEAU"
    pid_type = "place_idref_pid"
    model_cls = PlaceIdrefMetadata
    search = PlaceIdrefSearch

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
    def association_identifier(self):
        """Get associated identifier from identifiedBy."""
        pids = []
        for identified_by in self.get("identifiedBy", []):
            value = identified_by.get("value", "")
            if (
                identified_by.get("source") == "GND"
                and identified_by.get("type") == "bf:Nbn"
                and value.startswith("(DE-101)")
            ):
                pids.append(value.replace("(DE-101)", ""))
        if len(pids) > 1:
            current_app.logger.error(
                f"MULTIPLE ASSOCIATIONS FOUND FOR: {self.name} {self.pid} | {', '.join(pids)}"
            )
        if len(pids) == 1:
            return pids[0]

    @property
    def association_info(self):
        """Get associated record."""
        from rero_mef.places import PlaceGndRecord, PlaceGndSearch, PlaceMefRecord

        PlaceGndRecord.flush_indexes()
        return {
            "record": self.get_association_record(
                association_cls=PlaceGndRecord, association_search=PlaceGndSearch
            ),
            "record_cls": PlaceGndRecord,
            "search_cls": PlaceGndSearch,
            "mef_cls": PlaceMefRecord,
        }


class PlaceIdrefIndexer(PlaceIndexer):
    """Place IDREF indexer."""

    record_cls = PlaceIdrefRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(
            record_id_iterator, index=PlaceIdrefSearch.Meta.index, doc_type="pidref"
        )
