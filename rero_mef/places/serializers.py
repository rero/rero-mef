# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Record serialization."""

from invenio_records_rest.links import default_links_factory_with_additional
from invenio_records_rest.schemas import RecordSchemaJSONV1
from invenio_records_rest.serializers.json import JSONSerializer
from invenio_records_rest.serializers.response import (
    record_responsify,
    search_responsify,
)

from .mef.api import PlaceMefRecord


def add_links(pid, record):
    """Add MEF link to places."""
    links = {}
    for idx, mef_pid in enumerate(
        PlaceMefRecord.get_mef(record.pid, record.name, pid_only=True)
    ):
        number = f"-{idx}" if idx else ""
        links[f"mef{number}"] = "{scheme}://{host}/api/places/mef/" + str(mef_pid)

    link_factory = default_links_factory_with_additional(links)
    return link_factory(pid)


class ReroMefSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    def serialize(self, pid, record, links_factory=None, **kwargs):
        """Serialize a single record and persistent identifier.

        :param pid: Persistent identifier instance.
        :param record: Record instance.
        :param links_factory: Factory function for record links.
        """
        return super().serialize(
            pid=pid, record=record, links_factory=add_links, **kwargs
        )


json_ = ReroMefSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_place_response = record_responsify(json_, "application/rero+json")
json_place_search = search_responsify(json_, "application/rero+json")
