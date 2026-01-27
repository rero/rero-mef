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

"""Agent MEF aggregated records.

This module provides the MEF (Multilingual Entity File) aggregation layer for
agent entities. MEF records combine and link agent records from multiple
authority sources (VIAF, IdRef, GND, RERO) into unified entities.

The MEF record serves as the central hub that maintains relationships between
equivalent agent entities across different authority files, enabling
multilingual access and consistent referencing.
"""
