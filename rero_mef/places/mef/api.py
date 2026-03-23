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

    @classmethod
    def get_latest(cls, pid_type, pid, _visited=None):
        """Get latest Mef record for pid_type and pid.

        :param pid_type: pid type to use.
        :param pid: pid to use.
        :param _visited: set of already-seen pids used to break redirect cycles.
        :returns: latest record.
        """
        visited = _visited or set()
        if pid in visited:
            return {}
        visited.add(pid)
        search = PlaceMefSearch().filter({"term": {f"{pid_type}.pid": pid}})
        if search.count() > 0:
            data = next(search.scan()).to_dict()
            new_pid = None
            if relation_pid := data.get(pid_type, {}).get("relation_pid"):
                if relation_pid["type"] == "redirect_to":
                    new_pid = relation_pid["value"]
            elif pid_type == "idref":
                # Find new pid from redirect_pid redirect_from
                search = PlaceMefSearch().filter("term", idref__relation_pid__value=pid)
                if search.count() > 0:
                    new_data = next(search.scan()).to_dict()
                    new_pid = new_data.get("idref", {}).get("pid")
            return (
                cls.get_latest(pid_type=pid_type, pid=new_pid, _visited=visited)
                if new_pid
                else data
            )
        return {}


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
