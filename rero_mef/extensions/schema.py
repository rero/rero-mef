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

"""JSON Schema record extension."""

from urllib.parse import urljoin

from flask import current_app
from invenio_records.extensions import RecordExtension


class SchemaExtension(RecordExtension):
    """Invenio record extension that adds ``$schema`` to records.

    Automatically sets the ``$schema`` URL on every record before it is created or committed.  The URL is built from the
    record's provider ``pid_type`` and the Flask application configuration keys ``RECORDS_JSON_SCHEMA``,
    ``RERO_MEF_APP_BASE_URL`` and ``JSONSCHEMAS_ENDPOINT``.
    """

    def _set_schema(self, record):
        """Set ``$schema`` on *record* if it can be resolved."""
        if (entity := self._infer_entity(record)) and (
            schema_url := self._get_schema_url(entity)
        ):
            record["$schema"] = schema_url

    def pre_create(self, record, *args, **kwargs):
        """Hook called before a new record is persisted."""
        self._set_schema(record)
        # Sync to model.json so Invenio's use_model=True validation in Record.create() sees $schema
        if record.model is not None and "$schema" in record:
            record.model.data = dict(record)

    def pre_commit(self, record, *args, **kwargs):
        """Hook called before an existing record is committed."""
        self._set_schema(record)

    def _infer_entity(self, record):
        """Derive the entity pid_type from *record*'s provider.

        :param record: An Invenio Record instance.
        :returns: The ``pid_type`` string, or ``None``.
        """
        provider = getattr(record, "provider", None) or getattr(
            type(record), "provider", None
        )
        return getattr(provider, "pid_type", None) if provider else None

    def get_schema_url_for_entity(self, entity):
        """Get the full ``$schema`` URL for an entity type string.

        :param entity: The entity pid_type (e.g. ``"viaf"``, ``"aggnd"``).
        :returns: Absolute schema URL, or ``None`` if not configured.
        """
        return self._get_schema_url(entity)

    def _get_schema_url(self, entity):
        """Build the full ``$schema`` URL for *entity*.

        :param entity: The entity pid_type (e.g. ``"aggnd"``).
        :returns: Absolute schema URL, or ``None`` if not configured.
        """
        schemas = current_app.config.get("RECORDS_JSON_SCHEMA", {})
        base_url = current_app.config.get("RERO_MEF_APP_BASE_URL")
        endpoint = current_app.config.get("JSONSCHEMAS_ENDPOINT", "")
        schema = schemas.get(entity)
        if base_url and schema:
            return urljoin(base_url, f"{endpoint}{schema}")
        return None
