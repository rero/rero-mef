# -*- coding: utf-8 -*-
#
# This file is part of RERO MEF.
# Copyright (C) 2018 RERO.
#
# RERO MEF is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO MEF is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO MEF; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Record serialization."""

from flask import current_app, request
from invenio_records_rest.links import default_links_factory_with_additional
from invenio_records_rest.schemas import RecordSchemaJSONV1
from invenio_records_rest.serializers.json import JSONSerializer
from invenio_records_rest.serializers.response import record_responsify

from .authorities.api import MefRecord


def mef_link(pid, record):
    """Add mef link to agencys."""
    agencies = current_app.config.get('AGENCIES', {})
    current_agency = None
    for agency, agency_class in agencies.items():
        if agency_class == type(record):
            current_agency = agency
    mef_pid = MefRecord.get_mef_by_agency_pid(
        pid.pid_value,
        current_agency,
        pid_only=True
    )
    links = dict()
    if mef_pid:
        links = dict(mef='{scheme}://{host}/api/mef/' + str(mef_pid))
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
        if request and request.args.get('resolve'):
            record = record.replace_refs()
        if request and request.args.get('sources'):
            sources = []
            # TODO: add the list of sources into the current_app.config
            if 'rero' in record:
                sources.append('rero')
            if 'gnd' in record:
                sources.append('gnd')
            if 'bnf' in record:
                sources.append('bnf')
            record['sources'] = sources
        return super(
            ReroMefSerializer, self).serialize(
                pid, record, links_factory=mef_link, **kwargs)


json_v1 = ReroMefSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_v1_response = record_responsify(json_v1, 'application/rero+json')
