# -*- coding: utf-8 -*-
#
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

"""Agents."""

from .api import Action
from .gnd.api import AgentGndIndexer, AgentGndRecord, AgentGndSearch
from .idref.api import AgentIdrefIndexer, AgentIdrefRecord, AgentIdrefSearch
from .mef.api import AgentMefIndexer, AgentMefRecord, AgentMefSearch
from .rero.api import AgentReroIndexer, AgentReroRecord, AgentReroSearch
from .viaf.api import AgentViafIndexer, AgentViafRecord, AgentViafSearch

__all__ = ('AgentGndIndexer', 'AgentGndRecord', 'AgentGndSearch',
           'AgentIdrefIndexer', 'AgentIdrefRecord', 'AgentIdrefSearch',
           'AgentMefIndexer', 'AgentMefRecord', 'AgentMefSearch',
           'AgentReroIndexer', 'AgentReroRecord', 'AgentReroSearch',
           'AgentViafIndexer', 'AgentViafRecord', 'AgentViafSearch',
           'Action')
