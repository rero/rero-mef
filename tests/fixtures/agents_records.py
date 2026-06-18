# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Agents records."""

import pytest

from rero_mef.agents import (
    AgentGndRecord,
    AgentIdrefRecord,
    AgentMefRecord,
    AgentReroRecord,
    AgentViafRecord,
)

from ..utils import create_record


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


@pytest.fixture(scope="module")
def agent_gnd_crosstype_redirect_record(
    app,
    agent_gnd_crosstype_redirect_data,
    agent_gnd_crosstype_redirect_2_data,
    agent_gnd_crosstype_redirect_3_data,
    agent_gnd_record,
):
    """Create GND crosstype redirect records (bf:Organisation → bf:Person/Place)."""
    create_record(AgentGndRecord, agent_gnd_crosstype_redirect_2_data)
    create_record(AgentGndRecord, agent_gnd_crosstype_redirect_3_data)
    return create_record(AgentGndRecord, agent_gnd_crosstype_redirect_data)


@pytest.fixture(scope="module")
def agent_mef_crosstype_redirect_record(
    app,
    agent_mef_crosstype_redirect_data,
    agent_mef_crosstype_redirect_2_data,
    agent_mef_crosstype_redirect_3_data,
    agent_gnd_crosstype_redirect_record,
):
    """Create agent MEF crosstype redirect records."""
    create_record(AgentMefRecord, agent_mef_crosstype_redirect_2_data)
    create_record(AgentMefRecord, agent_mef_crosstype_redirect_3_data)
    return create_record(AgentMefRecord, agent_mef_crosstype_redirect_data)
