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

"""Deleted state propagation extension for MEF records."""

from copy import deepcopy

from invenio_records.extensions import RecordExtension


class DeletedStateExtension(RecordExtension):
    """Invenio record extension that propagates ``deleted`` state on MEF records.

    For MEF aggregation records (which link to source entities via ``$ref``), this extension automatically checks whether
    any linked source entity is marked as deleted and propagates that state to the MEF record.  If no source is deleted,
    any stale ``deleted`` field is removed.

    This extension only acts on records whose class defines an ``entities`` attribute (i.e. MEF record classes).
    Non-MEF records are passed through unchanged.
    """

    def _propagate_deleted(self, record):
        """Propagate ``deleted`` from resolved source entities to *record*.

        :param record: A MEF record instance with ``entities`` and ``replace_refs()``.
        :returns: ``True`` if the record was modified, ``False`` otherwise.
        """
        changed = False
        source_data = deepcopy(record).replace_refs()
        if sources := source_data.get("sources"):
            for source in sources:
                if deleted := source_data.get(source, {}).get("deleted"):
                    record["deleted"] = deleted
                    changed = True
                    break
            if not changed and record.get("deleted"):
                record.pop("deleted")
                changed = True
        return changed

    def _is_mef_record(self, record):
        """Check whether *record* is a MEF aggregation record."""
        return hasattr(type(record), "entities") and hasattr(record, "replace_refs")

    def pre_commit(self, record, *args, **kwargs):
        """Hook called before an existing record is committed."""
        if self._is_mef_record(record):
            self._propagate_deleted(record)

    def pre_create(self, record, *args, **kwargs):
        """Hook called before a new record is persisted."""
        if self._is_mef_record(record):
            self._propagate_deleted(record)
