# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_records.models import RecordMetadataBase


class PlaceMefMetadata(db.Model, RecordMetadataBase):
    """Represent a record metadata."""

    __tablename__ = "place_mef_metadata"
