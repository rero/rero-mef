# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2021 RERO
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

from flask import request, url_for
from invenio_records_rest.links import default_links_factory_with_additional
from invenio_records_rest.schemas import RecordSchemaJSONV1
from invenio_records_rest.serializers.json import JSONSerializer
from invenio_records_rest.serializers.response import record_responsify, \
    search_responsify

from ...utils import get_entity_classes


def add_links(pid, record):
    """Add VIAF links to MEF."""
    links = {}
    # viaf_pid = record.get('viaf_pid')
    # if viaf_pid:
    #     links['viaf'] = '{scheme}://{host}/api/places/viaf/' \
    #             + str(viaf_pid)
    #     viaf_url = current_app.confg.get('RERO_MEF_VIAF_BASE_URL')
    #     links['viaf.org'] = '{viaf_url}/viaf/' + str(viaf_pid)

    link_factory = default_links_factory_with_additional(links)
    return link_factory(pid)


# Nice to have direct working links in test server!
def local_link(place, name, record):
    """Change links to actual links."""
    if name in record:
        if ref := record[name].get('$ref'):
            my_pid = ref.split('/')[-1]
            url = url_for(
                f'invenio_records_rest.{place}_item',
                pid_value=my_pid,
                _external=True
            )
            record[name].update({'$ref': url})


class ReroMefSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    def serialize(self, pid, record, links_factory=None, **kwargs):
        """Serialize a single record and persistent identifier.

        :param pid: Persistent identifier instance.
        :param record: Record instance.
        :param links_factory: Factory function for record links.
        """
        rec = record
        if request:
            rec = rec.add_information(
                resolve=request.args.get(
                    'resolve',
                    default=False,
                    type=lambda v: v.lower() in ['true', '1']
                ),
                sources=request.args.get(
                    'sources',
                    default=False,
                    type=lambda v: v.lower() in ['true', '1']
                )
            )
            # because the replace_refs loose the record original model. We need
            # to reset it to have correct 'created'/'updated' output data
            rec.model = record.model
            if not rec.get('type'):
                rec['type'] = 'bf:Place'

        place_classes = get_entity_classes()
        for place, place_classe in place_classes.items():
            if place in ['pidref']:
                local_link(place, place_classe.name, rec)

        return super(ReroMefSerializer, self).serialize(
             pid=pid, record=rec, links_factory=add_links, **kwargs)


_json = ReroMefSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_place_mef_response = record_responsify(_json, 'application/rero+json')
json_place_mef_search = search_responsify(_json, 'application/rero+json')
