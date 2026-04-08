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

"""RERO Multilingual Entity File (MEF) system.

This package provides a comprehensive framework for aggregating and managing bibliographic entities (agents, concepts,
and places) from multiple international authority files including VIAF, IdRef, GND, and RERO.

The MEF system creates unified records by linking entities across different authority sources, enabling multilingual
access and consistent referencing in library systems.

Main components:
- Entity record management (agents, concepts, places)
- Authority file integration (VIAF, IdRef, GND, RERO)
- MEF aggregation and indexing
- REST API for entity access and updates
- MARC21 to JSON conversion
"""

from .ext import REROMEFAPP
from .version import __version__ as __version__

__all__ = ("REROMEFAPP",)
