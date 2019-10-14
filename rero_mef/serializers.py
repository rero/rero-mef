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

from flask import request, url_for
from invenio_records_rest.links import default_links_factory_with_additional
from invenio_records_rest.schemas import RecordSchemaJSONV1
from invenio_records_rest.serializers.json import JSONSerializer
from invenio_records_rest.serializers.response import record_responsify

from .authorities.mef.api import MefRecord, MefSearch
from .authorities.utils import get_agency_classes
from .authorities.viaf.api import ViafRecord


def add_links(pid, record):
    """Add mef link to agencys."""
    agency_class = get_agency_classes().get(pid.pid_type)
    links = {}
    if agency_class == MefRecord:
        links = dict(
            viaf='{scheme}://{host}/api/viaf/' + record.get('viaf_pid')
        )
    elif agency_class == ViafRecord:
        mef_pid_search = MefSearch().filter(
            'term', viaf_pid=record.get('pid')
        ).source(['pid']).scan()
        try:
            mef_pid = next(mef_pid_search).pid
            links = dict(mef='{scheme}://{host}/api/mef/' + mef_pid)
        except:
            pass
    else:
        mef_pid = MefRecord.get_mef_by_agency_pid(
            pid.pid_value,
            pid.pid_type,
            pid_only=True
        )
        if mef_pid:
            links = dict(mef='{scheme}://{host}/api/mef/' + str(mef_pid))
    link_factory = default_links_factory_with_additional(links)
    return link_factory(pid)


# Nice to have direct working links in test server!
def local_link(agency, record):
    """Change links to actual links."""
    if agency in record:
        ref = my_pid = record[agency].get('$ref')
        if ref:
            my_pid = ref.split('/')[-1]
            url = url_for(
                'invenio_records_rest.{agency}_item'.format(agency=agency),
                pid_value=my_pid,
                _external=True
            )
            record[agency].update({'$ref': url})


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
            if 'idref' in record:
                sources.append('idref')
            record['sources'] = sources

        for agency in ['bnf', 'gnd', 'idref', 'rero']:
            local_link(agency, record)

        return super(ReroMefSerializer, self).serialize(
            pid, record, links_factory=add_links, **kwargs
        )


json_v1 = ReroMefSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_v1_response = record_responsify(json_v1, 'application/rero+json')
