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

"""MARC21 to JSON conversion utilities.

This module provides tools for converting MARC21 bibliographic records to JSON format for different authority sources
(IdRef, GND, RERO).

Main components:
- MARC21 record parsing
- Field-specific conversion handlers
- Authority-specific conversion rules (agents, concepts, places)
- Validation and error handling
- Logging utilities
"""
