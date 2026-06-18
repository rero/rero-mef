# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""MD5 record extension for change detection."""

import hashlib
import json

from invenio_records.extensions import RecordExtension


class MD5Extension(RecordExtension):
    """Invenio record extension that adds an MD5 hash to records.

    Automatically computes and injects an ``md5`` field into every record before it is created or committed.  The hash
    is calculated over the JSON-serialised record (sorted keys, ``$schema`` excluded) so that it can be used for cheap
    change-detection during OAI harvesting.
    """

    def create_md5(self, record):
        """Compute the MD5 hex-digest for *record*.

        :param record: Record data (dict-like).
        :returns: Hex-encoded MD5 string.
        """
        return hashlib.md5(
            json.dumps(record, sort_keys=True, default=str).encode("utf-8"),
            usedforsecurity=False,
        ).hexdigest()

    def add_md5(self, record):
        """Add or refresh the ``md5`` field on *record*.

        Temporarily removes ``$schema`` before hashing so that schema URL changes do not invalidate the checksum.

        :param record: Record data (dict-like).
        :returns: The mutated *record*.
        """
        schema = record.pop("$schema", None)
        record.pop("md5", None)
        record["md5"] = self.create_md5(record)
        if schema is not None:
            record["$schema"] = schema
        return record

    def pre_create(self, record, *args, **kwargs):
        """Hook called before a new record is persisted."""
        self.add_md5(record)
        # Sync to model.json so Invenio's use_model=True validation in Record.create() sees md5
        if record.model is not None:
            record.model.data = dict(record)

    def pre_commit(self, record, *args, **kwargs):
        """Hook called before an existing record is committed."""
        self.add_md5(record)
        return record
