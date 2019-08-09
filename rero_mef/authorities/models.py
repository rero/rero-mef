# -*- coding: utf-8 -*-
#
# This file is part of RERO MEF.
# Copyright (C) 2018 RERO.
#
# RERO MEF is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO MEF is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO MEF; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Define relation between records and buckets."""

from __future__ import absolute_import

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class ViafIdentifier(RecordIdentifier):
    """Sequence generator for Viaf Authority identifiers."""

    __tablename__ = 'viaf_id'
    __mapper_args__ = {'concrete': True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, 'sqlite'),
        primary_key=True,
        autoincrement=True,
    )


class ViafMetadata(db.Model, RecordMetadataBase):
    """Viaf record metadata."""

    __tablename__ = 'viaf_metadata'


class BnfIdentifier(RecordIdentifier):
    """Sequence generator for BNF Authority identifiers."""

    __tablename__ = 'bnf_id'
    __mapper_args__ = {'concrete': True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, 'sqlite'),
        primary_key=True,
        autoincrement=True,
    )


class BnfMetadata(db.Model, RecordMetadataBase):
    """Bnf record metadata."""

    __tablename__ = 'bnf_metadata'


class GndIdentifier(RecordIdentifier):
    """Sequence generator for gnd Authority identifiers."""

    __tablename__ = 'gnd_id'
    __mapper_args__ = {'concrete': True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, 'sqlite'),
        primary_key=True,
        autoincrement=True,
    )


class GndMetadata(db.Model, RecordMetadataBase):
    """Gnd record metadata."""

    __tablename__ = 'gnd_metadata'


class MefIdentifier(RecordIdentifier):
    """Sequence generator for mef Authority identifiers."""

    __tablename__ = 'mef_id'
    __mapper_args__ = {'concrete': True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, 'sqlite'),
        primary_key=True,
        autoincrement=True,
    )


class MefMetadata(db.Model, RecordMetadataBase):
    """Mef record metadata."""

    __tablename__ = 'mef_metadata'


class ReroIdentifier(RecordIdentifier):
    """Sequence generator for rero Authority identifiers."""

    __tablename__ = 'rero_id'
    __mapper_args__ = {'concrete': True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, 'sqlite'),
        primary_key=True,
        autoincrement=True,
    )


class ReroMetadata(db.Model, RecordMetadataBase):
    """Rero record metadata."""

    __tablename__ = 'rero_metadata'


class MefAction(object):
    """Class holding all availabe Mef record creation actions."""

    CREATE = 'create'
    UPDATE = 'update'
    DISCARD = 'discard'
    DELETE = 'delete'


class AgencyAction(object):
    """Class holding all availabe agency record creation actions."""

    CREATE = 'create'
    UPDATE = 'update'
    DISCARD = 'discard'
    DELETE = 'delete'
