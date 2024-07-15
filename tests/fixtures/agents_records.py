# -*- coding: utf-8 -*-
#
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

"""Agents records."""

import pytest
from utils import create_record

from rero_mef.agents import (
    AgentGndRecord,
    AgentIdrefRecord,
    AgentMefRecord,
    AgentReroRecord,
    AgentViafRecord,
)


@pytest.fixture(scope="module")
def agent_idref_record(app, agent_idref_data):
    """Create a IdRef record."""
    return create_record(AgentIdrefRecord, agent_idref_data)


@pytest.fixture(scope="module")
def agent_idref_redirect_record(app, agent_idref_redirect_data):
    """Create a IdRef record."""
    return create_record(AgentIdrefRecord, agent_idref_redirect_data)


@pytest.fixture(scope="module")
def agent_gnd_record(app, agent_gnd_data):
    """Create a GND record."""
    return create_record(AgentGndRecord, agent_gnd_data)


@pytest.fixture(scope="module")
def agent_gnd_redirect_record(app, agent_gnd_redirect_data):
    """Create a GND record."""
    return create_record(AgentGndRecord, agent_gnd_redirect_data)


@pytest.fixture(scope="module")
def agent_rero_record(app, agent_rero_data):
    """Create a RERO record."""
    return create_record(AgentReroRecord, agent_rero_data)


@pytest.fixture(scope="module")
def agent_viaf_record(
    app, agent_viaf_data, agent_idref_record, agent_rero_record, agent_gnd_record
):
    """Create a VIAF record."""
    return create_record(AgentViafRecord, agent_viaf_data)


@pytest.fixture(scope="module")
def agent_viaf_gnd_redirect_record(
    app,
    agent_viaf_gnd_redirect_data,
    agent_idref_record,
    agent_rero_record,
    agent_gnd_redirect_record,
):
    """Create a VIAF record."""
    return create_record(AgentViafRecord, agent_viaf_gnd_redirect_data)


@pytest.fixture(scope="module")
def agent_viaf_idref_redirect_record(
    app,
    agent_viaf_idref_redirect_data,
    agent_idref_redirect_record,
    agent_rero_record,
    agent_gnd_redirect_record,
):
    """Create a VIAF record."""
    return create_record(AgentViafRecord, agent_viaf_idref_redirect_data)


@pytest.fixture(scope="module")
def agent_mef_record(app, agent_mef_data, agent_viaf_record):
    """Create a IdRef record."""
    return create_record(AgentMefRecord, agent_mef_data)


@pytest.fixture(scope="module")
def agent_mef_gnd_redirect_record(
    app, agent_mef_gnd_redirect_data, agent_viaf_gnd_redirect_record
):
    """Create a IdRef record."""
    return create_record(AgentMefRecord, agent_mef_gnd_redirect_data)


@pytest.fixture(scope="module")
def agent_mef_idref_redirect_record(
    app, agent_mef_idref_redirect_data, agent_viaf_idref_redirect_record
):
    """Create a IdRef record."""
    return create_record(AgentMefRecord, agent_mef_idref_redirect_data)
