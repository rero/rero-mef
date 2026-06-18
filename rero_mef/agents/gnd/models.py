# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class AgentGndIdentifier(RecordIdentifier):
    """Sequence generator for GND Authority identifiers."""

    __tablename__ = "agent_gnd_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class AgentGndMetadata(db.Model, RecordMetadataBase):
    """Represent a record metadata."""

    __tablename__ = "agent_gnd_metadata"
