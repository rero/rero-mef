# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2021 RERO
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


"""JSON resolvers."""

from __future__ import absolute_import, print_function, unicode_literals

import jsonresolver

from ..api import AgentViafRecord
from ....utils import get_host, resolve_record


@jsonresolver.route("/api/agents/viaf/<path:path>", host=get_host())
def resolve_rero(path):
    """Resolve VIAF records."""
    return resolve_record(path, AgentViafRecord)
