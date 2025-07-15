# RERO MEF
# Copyright (C) 2022 RERO
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

import jsonresolver

from ....utils import get_host, resolve_record
from ..api import ConceptIdrefRecord


@jsonresolver.route("/api/concepts/idref/<path:path>", host=get_host())
def resolve_idref(path):
    """Resolve Concepts records."""
    return resolve_record(path, ConceptIdrefRecord)
