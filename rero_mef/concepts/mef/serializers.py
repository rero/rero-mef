# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Record serialization."""

from flask import request, url_for
from invenio_records_rest.links import default_links_factory_with_additional
from invenio_records_rest.schemas import RecordSchemaJSONV1
from invenio_records_rest.serializers.json import JSONSerializer
from invenio_records_rest.serializers.response import (
    record_responsify,
    search_responsify,
)

from ...api_mef import _INDEX_ONLY_FIELDS
from ...utils import get_entity_classes


def add_links(pid, record):
    """Add VIAF links to MEF."""
    links = {}
    # viaf_pid = record.get('viaf_pid')
    # if viaf_pid:
    #     links['viaf'] = '{scheme}://{host}/api/concepts/viaf/' \
    #             + str(viaf_pid)
    #     viaf_url = current_app.confg.get('RERO_MEF_VIAF_BASE_URL')
    #     links['viaf.org'] = '{viaf_url}/viaf/' + str(viaf_pid)

    link_factory = default_links_factory_with_additional(links)
    return link_factory(pid)


# Nice to have direct working links in test server!
def local_link(concept, name, record):
    """Change links to actual links."""
    if name in record and (ref := record[name].get("$ref")):
        my_pid = ref.split("/")[-1]
        url = url_for(f"invenio_records_rest.{concept}_item", pid_value=my_pid, _external=True)
        record[name].update({"$ref": url})


class ReroMefSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    @staticmethod
    def preprocess_search_hit(pid, record_hit, links_factory=None, **kwargs):
        """Strip index-only bookkeeping fields from a search hit's metadata.

        ``record_hit["_source"]`` is the raw ES-indexed document, which
        carries fields injected at index time (entity, pid_numeric,
        sort_authorized_access_point, type_conflict) or by MD5Extension
        (md5) that a strict ``additionalProperties: false`` consumer schema
        (e.g. rero-ils's) rejects. Unlike the single-item ``serialize()``
        path, which resolves through ``add_information()``, search results
        go through this method instead and never touch that stripping.
        """
        record = JSONSerializer.preprocess_search_hit(pid, record_hit, links_factory=links_factory, **kwargs)
        for field in _INDEX_ONLY_FIELDS:
            record["metadata"].pop(field, None)
        return record

    def serialize(self, pid, record, links_factory=None, **kwargs):
        """Serialize a single record and persistent identifier.

        :param pid: Persistent identifier instance.
        :param record: Record instance.
        :param links_factory: Factory function for record links.
        """
        rec = record
        if request:
            rec = rec.add_information(
                resolve=request.args.get("resolve", default=False, type=lambda v: v.lower() in ["true", "1"]),
                sources=request.args.get("sources", default=False, type=lambda v: v.lower() in ["true", "1"]),
            )
            # because the replace_refs loose the record original model. We need
            # to reset it to have correct 'created'/'updated' output data
            rec.model = record.model
            if not rec.get("type"):
                rec["type"] = "bf:Topic"

        concept_classes = get_entity_classes()
        for concept, concept_classe in concept_classes.items():
            if concept in ["corero", "cidref", "cognd"]:
                local_link(concept, concept_classe.name, rec)

        return super().serialize(pid=pid, record=rec, links_factory=add_links, **kwargs)


_json = ReroMefSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_concept_mef_response = record_responsify(_json, "application/rero+json")
json_concept_mef_search = search_responsify(_json, "application/rero+json")
