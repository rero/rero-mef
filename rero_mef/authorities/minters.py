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

"""Identifier minters."""

from __future__ import absolute_import, print_function, unicode_literals

from functools import partial

from ..minters import id_minter
from .providers import BnfProvider, GndProvider, MefProvider, ReroProvider, \
    ViafProvider

viaf_id_minter = partial(id_minter, provider=ViafProvider,
                         recid_field='viaf_pid')
bnf_id_minter = partial(id_minter, provider=BnfProvider,
                        recid_field='pid')
gnd_id_minter = partial(id_minter, provider=GndProvider,
                        recid_field='pid')
rero_id_minter = partial(id_minter, provider=ReroProvider,
                         recid_field='pid')


def mef_id_minter(record_uuid, data, provider=MefProvider,
                  pid_key='pid', object_type='rec'):
    """RERIOLS Organisationid minter."""
    assert pid_key not in data
    provider = provider.create(
        object_type=object_type,
        object_uuid=record_uuid
    )
    pid = provider.pid
    data[pid_key] = pid.pid_value

    return pid
