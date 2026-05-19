# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

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
- Place*Indexer classes: Search indexing
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
