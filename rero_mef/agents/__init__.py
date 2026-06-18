# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Agent entity management for bibliographic authorities.

This module provides classes and functionality for managing agent entities (persons, organizations, families) from
multiple authority sources. Agents are aggregated into MEF records that link equivalent entities across different
international authority files.

Supported authority sources:
- VIAF (Virtual International Authority File)
- IdRef (French bibliographic agency)
- GND (German National Library)
- RERO (Swiss library network)

Main components:
- AgentMefRecord: Aggregated MEF records for agents
- Agent*Record classes: Authority-specific agent records
- Agent*Indexer classes: Elasticsearch indexing
- Agent*Search classes: Search and retrieval functionality
"""

from ..api import Action
from .gnd.api import AgentGndIndexer, AgentGndRecord, AgentGndSearch
from .idref.api import AgentIdrefIndexer, AgentIdrefRecord, AgentIdrefSearch
from .mef.api import AgentMefIndexer, AgentMefRecord, AgentMefSearch
from .rero.api import AgentReroIndexer, AgentReroRecord, AgentReroSearch
from .viaf.api import AgentViafIndexer, AgentViafRecord, AgentViafSearch

__all__ = (
    "Action",
    "AgentGndIndexer",
    "AgentGndRecord",
    "AgentGndSearch",
    "AgentIdrefIndexer",
    "AgentIdrefRecord",
    "AgentIdrefSearch",
    "AgentMefIndexer",
    "AgentMefRecord",
    "AgentMefSearch",
    "AgentReroIndexer",
    "AgentReroRecord",
    "AgentReroSearch",
    "AgentViafIndexer",
    "AgentViafRecord",
    "AgentViafSearch",
)
