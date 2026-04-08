# RERO MEF
# Copyright (C) 2026 RERO
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

"""RERO MEF invenio module declaration."""

from invenio_indexer.signals import before_record_index

from rero_mef.concepts.listener import enrich_concept_data
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

    def register_signals(self, app):
        """Register signal handlers for data enrichment.

        Connects enrichment functions to the before_record_index signal to enhance concept and place data before
        indexing in Elasticsearch.

        :param app: Flask application instance.
        """
        before_record_index.connect(enrich_concept_data, sender=app)
        before_record_index.connect(enrich_place_data, sender=app)
