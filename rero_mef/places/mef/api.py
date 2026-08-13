# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating MEF records."""

from invenio_search.api import RecordsSearch

from rero_mef.api_mef import EntityMefRecord, MefIndexer

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
        return super().update(data=data, commit=commit, dbcommit=dbcommit, reindex=reindex)

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


class PlaceMefIndexer(MefIndexer):
    """Place MEF indexer."""

    record_cls = PlaceMefRecord
