# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Concept entity management for subject authorities.

This module provides classes and functionality for managing concept entities (subjects, topics, genres) from multiple
authority sources. Concepts are aggregated into MEF records that link equivalent subject headings across different
authority files.

Supported authority sources:
- IdRef (French bibliographic agency)
- GND (German National Library)
- RERO (Swiss library network)

Main components:
- ConceptMefRecord: Aggregated MEF records for concepts
- Concept*Record classes: Authority-specific concept records
- Concept*Indexer classes: Search indexing
- Concept*Search classes: Search and retrieval functionality
"""

from ..api import Action
from .gnd.api import ConceptGndIndexer, ConceptGndRecord, ConceptGndSearch
from .idref.api import ConceptIdrefIndexer, ConceptIdrefRecord, ConceptIdrefSearch
from .mef.api import ConceptMefIndexer, ConceptMefRecord, ConceptMefSearch
from .rero.api import ConceptReroIndexer, ConceptReroRecord, ConceptReroSearch

__all__ = (
    "Action",
    "ConceptGndIndexer",
    "ConceptGndRecord",
    "ConceptGndSearch",
    "ConceptIdrefIndexer",
    "ConceptIdrefRecord",
    "ConceptIdrefSearch",
    "ConceptMefIndexer",
    "ConceptMefRecord",
    "ConceptMefSearch",
    "ConceptReroIndexer",
    "ConceptReroRecord",
    "ConceptReroSearch",
)
