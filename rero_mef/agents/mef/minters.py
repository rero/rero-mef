# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2020 RERO
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

"""Identifier minters."""

from __future__ import absolute_import, print_function, unicode_literals

from .providers import MefProvider


def mef_id_minter(record_uuid, data, provider=MefProvider,
                  pid_key='pid', object_type='rec'):
    """RERIOLS MEF id minter."""
    assert pid_key not in data
    provider = provider.create(
        object_type=object_type,
        object_uuid=record_uuid
    )
    pid = provider.pid
    data[pid_key] = pid.pid_value

    return pid
