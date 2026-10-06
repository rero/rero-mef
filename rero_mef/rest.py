# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Conditional GET for MEF records covering their linked source records."""

from invenio_records_rest.serializers.response import record_responsify
from invenio_records_rest.views import RecordResource, need_record_permission, pass_record

MEF_ITEM_ENDPOINTS = ("mef_item", "comef_item", "plmef_item")


class MefRecordResource(RecordResource):
    """Item resource whose ETag and last-modified date cover the linked sources."""

    @pass_record
    @need_record_permission("read_permission_factory")
    def get(self, pid, record, **kwargs):
        """Get a MEF record, answering 304 only when neither it nor its sources changed."""
        etag, updated = record.http_validators
        self.check_etag(etag, weak=True)
        self.check_if_modified_since(updated, etag=etag)
        return self.make_response(pid, record, links_factory=self.links_factory)


def mef_record_responsify(serializer, mimetype):
    """Create a MEF record response factory using the record's HTTP validators.

    :param serializer: Serializer instance.
    :param mimetype: MIME type of response.
    :returns: Function that generates a record HTTP response.
    """
    base = record_responsify(serializer, mimetype)

    def view(pid, record, code=200, headers=None, links_factory=None):
        response = base(pid, record, code=code, headers=headers, links_factory=links_factory)
        etag, updated = record.http_validators
        response.set_etag(etag)
        response.last_modified = updated
        return response

    return view


def finalize_app(app):
    """Serve the MEF item endpoints with ``MefRecordResource``.

    Flask instantiates ``view.view_class`` on each request, so the arguments invenio-records-rest built the views with
    are kept.
    """
    for endpoint in MEF_ITEM_ENDPOINTS:
        if view := app.view_functions.get(f"invenio_records_rest.{endpoint}"):
            view.view_class = MefRecordResource
