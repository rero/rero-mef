# RERO MEF
# Copyright (C) 2026 RERO
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

"""Invenio record extensions for RERO MEF."""

from .deleted import DeletedStateExtension
from .md5 import MD5Extension
from .schema import SchemaExtension

__all__ = ["DeletedStateExtension", "MD5Extension", "SchemaExtension"]
