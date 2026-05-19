# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""RERO MEF invenio module declaration."""

from flask.json.provider import DefaultJSONProvider
from invenio_indexer.signals import before_record_index
from jsonref import JsonRef

from rero_mef.concepts.listener import enrich_concept_data
from rero_mef.listener import enrich_mef_data
from rero_mef.places.listener import enrich_place_data


class MEFJSONProvider(DefaultJSONProvider):
    """JSON provider that serializes the references jsonref inlines.

    With ``JSONSCHEMAS_REPLACE_REFS``, ``/schemas`` inlines the ``$ref`` of a schema as lazy ``JsonRef`` proxies,
    which the default provider cannot serialize below the top level.
    """

    @staticmethod
    def default(o):
        """Serialize a ``JsonRef`` as the object it points to.

        :param o: Object the JSON encoder cannot serialize.
        :returns: A serializable object.
        """
        if isinstance(o, JsonRef):
            return o.__subject__
        return DefaultJSONProvider.default(o)


class REROMEFAPP:
    """RERO MEF Flask extension.

    Provides initialization and setup for the RERO MEF application, including signal registration for data enrichment
    during indexing.
    """

    def __init__(self, app=None):
        """Initialize the RERO MEF extension.

        :param app: Flask application instance. If provided, initializes the extension immediately.
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize Flask application with RERO MEF extension.

        Registers this extension with the Flask application's extension registry and connects signal handlers.

        :param app: Flask application instance.
        """
        app.extensions["rero-mef"] = self
        app.json = MEFJSONProvider(app)
        self.register_signals(app)

    def register_signals(self, app):
        """Register signal handlers for data enrichment.

        Connects enrichment functions to the before_record_index signal to enhance concept and place data before
        indexing in Search.

        :param app: Flask application instance.
        """
        before_record_index.connect(enrich_mef_data, sender=app)
        before_record_index.connect(enrich_concept_data, sender=app)
        before_record_index.connect(enrich_place_data, sender=app)
