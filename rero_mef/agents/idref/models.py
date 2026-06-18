# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class AgentIdrefIdentifier(RecordIdentifier):
    """Sequence generator for IDREF agent identifiers."""

    __tablename__ = "agent_idref_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class AgentIdrefMetadata(db.Model, RecordMetadataBase):
    """Represent a record metadata."""

    __tablename__ = "agent_idref_metadata"
