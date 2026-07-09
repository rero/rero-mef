# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating MEF records."""

from copy import deepcopy

from flask import current_app
from invenio_search.api import RecordsSearch

from rero_mef.api import EntityIndexer
from rero_mef.api_mef import EntityMefRecord

from .fetchers import mef_id_fetcher
from .minters import mef_id_minter
from .models import PlaceMefMetadata
from .providers import PlaceMefProvider


class PlaceMefSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = "places_mef"
        doc_types = None
        fields = ("*",)
        facets = {}

        default_filter = None


class PlaceMefRecord(EntityMefRecord):
    """Mef place class."""

    minter = mef_id_minter
    fetcher = mef_id_fetcher
    provider = PlaceMefProvider
    name = "mef"
    model_cls = PlaceMefMetadata
    search = PlaceMefSearch
    mef_type = "PLACES"
    entities = ["idref", "gnd"]

    def update(self, data, commit=False, dbcommit=False, reindex=False):
        """Update data for record.

        :param data: a dict data to update the record.
        :param commit: if True push the db transaction.
        :param dbcommit: make the change effective in db.
        :param reindex: reindex the record.
        :returns: the modified record
        """
        data["type"] = "bf:Place"
        return super().update(
            data=data, commit=commit, dbcommit=dbcommit, reindex=reindex
        )

    @classmethod
    def create(
        cls,
        data,
        id_=None,
        delete_pid=False,
        dbcommit=False,
        reindex=False,
        md5=True,
        **kwargs,
    ):
        """Create a new place record."""
        data["type"] = "bf:Place"
        return super().create(
            data=data,
            id_=id_,
            delete_pid=delete_pid,
            dbcommit=dbcommit,
            reindex=reindex,
            md5=False,
            **kwargs,
        )

    def replace_refs(self):
        """Replace $ref with real data."""
        data = deepcopy(self)
        data = super().replace_refs()
        data["sources"] = [place for place in self.entities if data.get(place)]
        return data

    def add_information(self, resolve=False, sources=False):
        """Add information to record.

        Sources will be also added if resolve is True.
        :param resolve: resolve $refs
        :param sources: Add sources information to record
        :returns: record
        """
        replace_refs_data = PlaceMefRecord(deepcopy(self).replace_refs())
        data = replace_refs_data if resolve else deepcopy(self)
        my_sources = []
        for place in self.entities:
            if place_data := data.get(place):
                # we got a error status in data
                if place_data.get("status"):
                    data.pop(place)
                    current_app.logger.error(
                        f"MEF replace refs {data.get('pid')} {place}"
                        f" status: {place_data.get('status')}"
                        f" {place_data.get('message')}"
                    )
                else:
                    my_sources.append(place)
                for place in self.entities:
                    if metadata := replace_refs_data.get(place, {}).get("metadata"):
                        data[place] = metadata
        if my_sources and (resolve or sources):
            data["sources"] = my_sources
        return data


class PlaceMefIndexer(EntityIndexer):
    """Place MEF indexer."""

    record_cls = PlaceMefRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(
            record_id_iterator, index=PlaceMefSearch.Meta.index, doc_type="plmef"
        )
