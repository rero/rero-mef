# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2020 RERO
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

"""Record serialization."""


import contextlib

from flask import current_app
from invenio_records_rest.links import default_links_factory_with_additional
from invenio_records_rest.schemas import RecordSchemaJSONV1
from invenio_records_rest.serializers.json import JSONSerializer
from invenio_records_rest.serializers.response import (
    record_responsify,
    search_responsify,
)

from .mef.api import AgentMefRecord
from .viaf.api import AgentViafSearch


def add_links(pid, record):
    """Add MEF link to agents."""
    links = {}
    for idx, mef_pid in enumerate(
        AgentMefRecord.get_mef(record.pid, record.name, pid_only=True)
    ):
        number = f"-{idx}" if idx else ""
        links[f"mef{number}"] = "{scheme}://{host}/api/agents/mef/" + str(mef_pid)

    with contextlib.suppress(Exception):
        query = (
            AgentViafSearch()
            .filter({"term": {record.viaf_pid_name: pid.pid_value}})
            .params(preserve_order=True)
            .sort({"_updated": {"order": "desc"}})
            .source("pid")
        )
        viaf_pid = next(query.scan()).pid
        links["viaf"] = "{scheme}://{host}/api/agents/viaf/" + str(viaf_pid)
        viaf_url = current_app.config.get("RERO_MEF_VIAF_BASE_URL")
        links["viaf.org"] = f"{viaf_url}/viaf/{str(viaf_pid)}"
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
        return super(ReroMefSerializer, self).serialize(
            pid=pid, record=record, links_factory=add_links, **kwargs
        )


json_ = ReroMefSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_agent_response = record_responsify(json_, "application/rero+json")
json_agent_search = search_responsify(json_, "application/rero+json")
