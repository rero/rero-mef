# RERO MEF
# Copyright (C) 2024 RERO
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

"""Place entity management for geographic authorities.

This module provides classes and functionality for managing place entities (geographic locations, jurisdictions) from
multiple authority sources. Places are aggregated into MEF records that link equivalent geographic entities across
different authority files.

Supported authority sources:
- IdRef (French bibliographic agency)
- GND (German National Library)

Main components:
- PlaceMefRecord: Aggregated MEF records for places
- Place*Record classes: Authority-specific place records
- Place*Indexer classes: Elasticsearch indexing
- Place*Search classes: Search and retrieval functionality
"""

from ..api import Action
from .gnd.api import PlaceGndIndexer, PlaceGndRecord, PlaceGndSearch
from .idref.api import PlaceIdrefIndexer, PlaceIdrefRecord, PlaceIdrefSearch
from .mef.api import PlaceMefIndexer, PlaceMefRecord, PlaceMefSearch

__all__ = (
    "Action",
    "PlaceGndIndexer",
    "PlaceGndRecord",
    "PlaceGndSearch",
    "PlaceIdrefIndexer",
    "PlaceIdrefRecord",
    "PlaceIdrefSearch",
    "PlaceMefIndexer",
    "PlaceMefRecord",
    "PlaceMefSearch",
)
