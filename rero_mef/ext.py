# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""RERO MEF invenio module declaration."""

from invenio_indexer.signals import before_record_index
from invenio_search import current_search_client
from opensearchpy.exceptions import ConnectionError as OSConnectionError
from opensearchpy.exceptions import NotFoundError

from rero_mef.concepts.listener import enrich_concept_data
from rero_mef.listener import enrich_mef_data
from rero_mef.places.listener import enrich_place_data


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
        self.register_signals(app)
        self.ensure_all_mef_alias(app)

    def register_signals(self, app):
        """Register signal handlers for data enrichment.

        Connects enrichment functions to the before_record_index signal to enhance concept and place data before
        indexing in Search.

        :param app: Flask application instance.
        """
        before_record_index.connect(enrich_mef_data, sender=app)
        before_record_index.connect(enrich_concept_data, sender=app)
        before_record_index.connect(enrich_place_data, sender=app)

    def ensure_all_mef_alias(self, app):
        """Ensure the all_mef alias points to all MEF indexes.

        The alias targets the concrete indexes currently behind these aliases:
        - mef
        - concepts_mef
        - places_mef
        """
        target_aliases = ("mef", "concepts_mef", "places_mef")
        alias_name = "all_mef"

        with app.app_context():
            if "invenio-search" not in app.extensions:
                app.logger.info(
                    "Skipping %s alias setup: invenio-search extension is not initialized yet.",
                    alias_name,
                )
                return

            try:
                search_client = current_search_client
            except RuntimeError, AttributeError:
                app.logger.info(
                    "Skipping %s alias setup: search client is not available yet.",
                    alias_name,
                )
                return

            try:
                # Probe connectivity — OpenSearch may not be running during image build.
                search_client.indices.exists_alias(name=alias_name)
            except OSConnectionError:
                app.logger.info(
                    "Skipping %s alias setup: OpenSearch is not reachable.",
                    alias_name,
                )
                return

            for target in target_aliases:
                try:
                    # Resolve alias -> concrete indexes.
                    alias_mapping = search_client.indices.get_alias(name=target)
                except NotFoundError:
                    alias_mapping = {}

                index_names = list(alias_mapping.keys())
                if not index_names:
                    # Fallback: target can itself be a concrete index name.
                    index_names = [target]

                for index_name in index_names:
                    try:
                        search_client.indices.put_alias(
                            index=index_name,
                            name=alias_name,
                        )
                    except NotFoundError as err:
                        app.logger.warning(
                            "Could not attach alias %s to %s: %s",
                            alias_name,
                            index_name,
                            err,
                        )
