# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating Gnd agent."""

from invenio_search.api import RecordsSearch

from rero_mef.places.api import PlaceIndexer, PlaceRecord

from .fetchers import gnd_id_fetcher
from .minters import gnd_id_minter
from .models import PlaceGndMetadata
from .providers import PlaceGndProvider


class PlaceGndSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = "places_gnd"
        doc_types = None
        fields = ("*",)
        facets = {}

        default_filter = None


class PlaceGndRecord(PlaceRecord):
    """Places Authority class."""

    minter = gnd_id_minter
    fetcher = gnd_id_fetcher
    provider = PlaceGndProvider
    name = "gnd"
    viaf_source_code = "RAMEAU"
    pid_type = "place_gnd_pid"
    model_cls = PlaceGndMetadata
    search = PlaceGndSearch

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
        return self.pid

    @property
    def association_info(self):
        """Get associated record."""
        from rero_mef.places import PlaceIdrefRecord, PlaceIdrefSearch, PlaceMefRecord

        PlaceIdrefRecord.flush_indexes()
        return {
            "identifier": self.association_identifier,
            "record": self.get_association_record(
                association_cls=PlaceIdrefRecord, association_search=PlaceIdrefSearch
            ),
            "record_cls": PlaceIdrefRecord,
            "search_cls": PlaceIdrefSearch,
            "mef_cls": PlaceMefRecord,
        }


class PlaceGndIndexer(PlaceIndexer):
    """Place GND indexer."""

    record_cls = PlaceGndRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(
            record_id_iterator, index=PlaceGndSearch.Meta.index, doc_type="plgnd"
        )
