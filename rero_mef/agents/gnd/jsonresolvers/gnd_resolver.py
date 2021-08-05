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


"""Json resolvers."""

from __future__ import absolute_import, print_function, unicode_literals

import jsonresolver

from rero_mef.utils import get_host, resolve_record

from ..api import AgentGndRecord


@jsonresolver.route('/api/agents/gnd/<path:path>', host=get_host())
def resolve_gnd(path):
    """Resolve GND records."""
    return resolve_record(path, AgentGndRecord)
