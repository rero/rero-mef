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

"""Identifier provider."""

from __future__ import absolute_import, print_function

from invenio_pidstore.models import PIDStatus
from invenio_pidstore.providers.base import BaseProvider

from .models import BnfIdentifier, GndIdentifier, MefIdentifier, \
    ReroIdentifier, ViafIdentifier


class MefProvider(BaseProvider):
    """Mef identifier provider."""

    pid_type = 'mef'
    """Type of persistent identifier."""

    pid_identifier = MefIdentifier.__tablename__
    """Identifier for table name"""

    pid_provider = None
    """Provider name.

    The provider name is not recorded in the PID since the provider does not
    provide any additional features besides creation of Document ids.
    """

    default_status = PIDStatus.REGISTERED
    """Mef IDs are by default registered immediately."""

    @classmethod
    def create(cls, object_type=None, object_uuid=None, **kwargs):
        """Create a new Mef Authority identifier."""
        assert 'pid_value' not in kwargs
        kwargs['pid_value'] = str(MefIdentifier.next())
        kwargs.setdefault('status', cls.default_status)
        if object_type and object_uuid:
            kwargs['status'] = PIDStatus.REGISTERED
        return super(MefProvider, cls).create(
            object_type=object_type, object_uuid=object_uuid, **kwargs)


class ReroProvider(BaseProvider):
    """Rero identifier provider."""

    pid_type = 'rero'
    """Type of persistent identifier."""

    pid_identifier = ReroIdentifier.__tablename__
    """Identifier for table name"""

    pid_provider = None
    """Provider name.

    The provider name is not recorded in the PID since the provider does not
    provide any additional features besides creation of Document ids.
    """

    default_status = PIDStatus.REGISTERED
    """Rero IDs are by default registered immediately."""


class GndProvider(BaseProvider):
    """Gnd identifier provider."""

    pid_type = 'gnd'
    """Type of persistent identifier."""

    pid_identifier = GndIdentifier.__tablename__
    """Identifier for table name"""

    pid_provider = None
    """Provider name.

    The provider name is not recorded in the PID since the provider does not
    provide any additional features besides creation of Document ids.
    """

    default_status = PIDStatus.REGISTERED
    """Gnd IDs are by default registered immediately."""


class BnfProvider(BaseProvider):
    """Bnf identifier provider."""

    pid_type = 'bnf'
    """Type of persistent identifier."""

    pid_identifier = BnfIdentifier.__tablename__
    """Identifier for table name"""

    pid_provider = None
    """Provider name.

    The provider name is not recorded in the PID since the provider does not
    provide any additional features besides creation of Document ids.
    """

    default_status = PIDStatus.REGISTERED
    """Bnf IDs are by default registered immediately."""


class ViafProvider(BaseProvider):
    """Viaf identifier provider."""

    pid_type = 'viaf'
    """Type of persistent identifier."""

    pid_identifier = ViafIdentifier.__tablename__
    """Identifier for table name"""

    pid_provider = None
    """Provider name.

    The provider name is not recorded in the PID since the provider does not
    provide any additional features besides creation of Document ids.
    """

    default_status = PIDStatus.REGISTERED
    """Viaf IDs are by default registered immediately."""
