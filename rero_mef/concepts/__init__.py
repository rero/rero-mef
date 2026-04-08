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
- Concept*Indexer classes: Elasticsearch indexing
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
