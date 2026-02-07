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

"""Test agents MEF api."""

import os
from copy import deepcopy
from unittest import mock

import pytest
from click.testing import CliRunner
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier

from rero_mef.agents import (
    Action,
    AgentMefRecord,
    AgentReroRecord,
    AgentViafRecord,
    AgentViafSearch,
)
from rero_mef.agents.viaf.api import RetryableVIAFError
from rero_mef.cli import init_oai_harvest_config
from rero_mef.monitoring import Monitoring

from ...utils import mock_response


@pytest.fixture(autouse=True)
def _disable_viaf_request_delay(app):
    """Disable VIAF per-request sleep for fast and deterministic tests."""
    old_delay = app.config.get("RERO_MEF_VIAF_REQUEST_DELAY")
    app.config["RERO_MEF_VIAF_REQUEST_DELAY"] = 0
    try:
        yield
    finally:
        app.config["RERO_MEF_VIAF_REQUEST_DELAY"] = old_delay


def test_get_pids_with_multiple_viaf(app, agent_viaf_record):
    """Test get pids with multiple MEF."""
    multiple_pids = AgentViafRecord.get_pids_with_multiple_viaf()
    assert multiple_pids == {"gnd_pid": {}, "idref_pid": {}, "rero_pid": {}}

    data = deepcopy(agent_viaf_record)
    data["pid"] = "test"
    viaf_record = AgentViafRecord.create(data=data, dbcommit=True, reindex=True)
    AgentViafRecord.flush_indexes()
    multiple_pids = AgentViafRecord.get_pids_with_multiple_viaf()
    assert multiple_pids == {
        "gnd_pid": {"12391664X": ["66739143", "test"]},
        "idref_pid": {"069774331": ["66739143", "test"]},
        "rero_pid": {"A023655346": ["66739143", "test"]},
    }
    viaf_record.delete(dbcommit=True, delindex=True)
    assert AgentViafRecord.get_record_by_pid("test") is None
    assert AgentViafSearch().filter("term", pid="test").count() == 0
    with pytest.raises(PIDDoesNotExistError):
        PersistentIdentifier.get("viaf", "test")
    # delete created MEF record
    for mef_record in AgentMefRecord.get_all_records():
        mef_record.delete(dbcommit=True, delindex=True, force=True)


@mock.patch("requests.Session.get")
def test_get_online(mock_get, app, agent_viaf_online_response):
    """Test get VIAF online."""
    mock_get.return_value = mock_response(json_data=agent_viaf_online_response)
    data, msg = AgentViafRecord.get_online_record("SUDOC", "076515788")
    assert data == {
        "bnf": "http://catalogue.bnf.fr/ark:/12148/cb125442835",
        "bnf_pid": "12544283",
        "gnd": "http://d-nb.info/gnd/1248506-8",
        "gnd_pid": "969004222",
        "pid": "124294761",
        "idref_pid": "076515788",
    }
    assert msg == (
        "VIAF get: 076515788       "
        "http://www.viaf.org/viaf/sourceID/SUDOC%7C076515788 | OK"
    )

    mock_get.return_value = mock_response(json_data=agent_viaf_online_response)
    data, msg = AgentViafRecord.get_online_record(
        "SUDOC", "076515788", rec_format="raw"
    )
    assert data == agent_viaf_online_response
    assert msg == (
        "VIAF get: 076515788       "
        "http://www.viaf.org/viaf/sourceID/SUDOC%7C076515788 | OK"
    )


def test_create_mef_and_agents(
    app, agent_viaf_record, agent_gnd_record, agent_rero_record, agent_idref_record
):
    """Test create MEF and agents."""
    monitor = Monitoring()

    actions = agent_viaf_record.create_mef_and_agents(dbcommit=True, reindex=True)
    mef_pid = AgentMefRecord.get_mef(
        entity_pid=agent_viaf_record.pid,
        entity_name=agent_viaf_record.name,
        pid_only=True,
    )[0]
    assert actions == {
        "069774331": {
            "MEF": {mef_pid: Action.CREATE},
            "action": Action.NOT_ONLINE,
            "source": "idref",
        },
        "12391664X": {
            "MEF": {mef_pid: Action.UPDATE},
            "action": Action.NOT_ONLINE,
            "source": "gnd",
        },
        "A023655346": {
            "MEF": {mef_pid: Action.UPDATE},
            "action": Action.NOT_ONLINE,
            "source": "rero",
        },
    }

    assert AgentMefRecord.count() == 1
    info = monitor.check_mef()
    assert info == {
        "aggnd": {"db": 1, "index": "aggnd", "mef": 1, "mef-db": 0},
        "agrero": {"db": 1, "index": "agrero", "mef": 1, "mef-db": 0},
        "aidref": {"db": 1, "index": "aidref", "mef": 1, "mef-db": 0},
        "cidref": {"db": 0, "index": "cidref", "mef": 0, "mef-db": 0},
        "cognd": {"db": 0, "index": "cognd", "mef": 0, "mef-db": 0},
        "corero": {"db": 0, "index": "corero", "mef": 0, "mef-db": 0},
        "pidref": {"db": 0, "index": "pidref", "mef": 0, "mef-db": 0},
        "plgnd": {"db": 0, "index": "plgnd", "mef": 0, "mef-db": 0},
    }
    # Change RERO in VIAF:
    agent_viaf_record["rero_pid"] = "AXXXXXXXXX"
    agent_viaf_record.update(data=agent_viaf_record, dbcommit=True, reindex=True)
    actions = agent_viaf_record.create_mef_and_agents(dbcommit=True, reindex=True)
    assert actions == {
        "069774331": {
            "MEF": {mef_pid: Action.UPDATE},
            "action": Action.NOT_ONLINE,
            "source": "idref",
        },
        "12391664X": {
            "MEF": {mef_pid: Action.UPDATE},
            "action": Action.NOT_ONLINE,
            "source": "gnd",
        },
        "A023655346": {
            "MEF": {mef_pid: Action.DELETE, str(int(mef_pid) + 1): Action.CREATE},
            "action": Action.DISCARD,
            "source": "rero",
        },
        "AXXXXXXXXX": {"action": Action.NOT_FOUND, "source": "rero"},
    }
    assert AgentMefRecord.count() == 2
    info = monitor.check_mef()
    assert info == {
        "aggnd": {"db": 1, "index": "aggnd", "mef": 1, "mef-db": 0},
        "agrero": {"db": 1, "index": "agrero", "mef": 1, "mef-db": 0},
        "aidref": {"db": 1, "index": "aidref", "mef": 1, "mef-db": 0},
        "cidref": {"db": 0, "index": "cidref", "mef": 0, "mef-db": 0},
        "cognd": {"db": 0, "index": "cognd", "mef": 0, "mef-db": 0},
        "corero": {"db": 0, "index": "corero", "mef": 0, "mef-db": 0},
        "pidref": {"db": 0, "index": "pidref", "mef": 0, "mef-db": 0},
        "plgnd": {"db": 0, "index": "plgnd", "mef": 0, "mef-db": 0},
    }

    # Create missing RERO record
    agent_rero_data_2 = deepcopy(agent_rero_record)
    agent_rero_data_2["pid"] = "AXXXXXXXXX"
    agent_rero_record_2 = AgentReroRecord.create(
        data=agent_rero_data_2, dbcommit=True, reindex=True
    )
    agent_rero_record_2.create_or_update_mef(dbcommit=True, reindex=True)
    assert AgentMefRecord.count() == 2

    # delete GND from VIAF:
    agent_viaf_record = AgentViafRecord.get_record_by_pid(agent_viaf_record.pid)
    gnd_pid = agent_viaf_record.pop("gnd_pid")
    agent_viaf_record["rero_pid"] = "A023655346"
    agent_viaf_record.update(data=agent_viaf_record, dbcommit=True, reindex=True)
    actions = agent_viaf_record.create_mef_and_agents(dbcommit=True, reindex=True)
    assert actions == {
        "069774331": {
            "MEF": {mef_pid: Action.UPDATE},
            "action": Action.NOT_ONLINE,
            "source": "idref",
        },
        "12391664X": {
            "MEF": {mef_pid: Action.DELETE, str(int(mef_pid) + 2): Action.CREATE},
            "action": Action.DISCARD,
            "source": "gnd",
        },
        "A023655346": {
            "MEF": {mef_pid: Action.UPDATE, str(int(mef_pid) + 1): Action.DISCARD},
            "action": Action.NOT_ONLINE,
            "source": "rero",
        },
        "AXXXXXXXXX": {
            "MEF": {mef_pid: Action.DELETE, str(int(mef_pid) + 3): Action.CREATE},
            "action": Action.DISCARD,
            "source": "rero",
        },
    }
    assert AgentMefRecord.count() == 4
    info = monitor.check_mef()
    assert info == {
        "aggnd": {"db": 1, "index": "aggnd", "mef": 1, "mef-db": 0},
        "agrero": {"db": 2, "index": "agrero", "mef": 2, "mef-db": 0},
        "aidref": {"db": 1, "index": "aidref", "mef": 1, "mef-db": 0},
        "cidref": {"db": 0, "index": "cidref", "mef": 0, "mef-db": 0},
        "cognd": {"db": 0, "index": "cognd", "mef": 0, "mef-db": 0},
        "corero": {"db": 0, "index": "corero", "mef": 0, "mef-db": 0},
        "pidref": {"db": 0, "index": "pidref", "mef": 0, "mef-db": 0},
        "plgnd": {"db": 0, "index": "plgnd", "mef": 0, "mef-db": 0},
    }

    # readd GND to VIAF and add wrongly VIAF pid to GND MEF record:
    mef_gnd_record = AgentMefRecord.get_record_by_pid("4")
    mef_gnd_record["viaf_pid"] = agent_viaf_record.pid
    mef_gnd_record.update(mef_gnd_record, dbcommit=True, reindex=True)
    xxx, action = agent_gnd_record.create_or_update_mef(dbcommit=True, reindex=True)
    mef_record = AgentMefRecord.get_record_by_pid(mef_pid)
    assert "gnd" not in mef_record
    assert "idref" in mef_record
    assert "rero" in mef_record
    agent_viaf_record = AgentViafRecord.get_record_by_pid(agent_viaf_record.pid)
    agent_viaf_record["gnd_pid"] = gnd_pid
    agent_viaf_record.update(data=agent_viaf_record, dbcommit=True, reindex=True)
    actions = agent_viaf_record.create_mef_and_agents(dbcommit=True, reindex=True)
    mef_pid_new = AgentMefRecord.get_mef(
        entity_pid=agent_viaf_record.pid,
        entity_name=agent_viaf_record.name,
        pid_only=True,
    )[0]
    mef_record = AgentMefRecord.get_record_by_pid(mef_pid_new)
    assert "gnd" in mef_record
    assert "idref" in mef_record
    assert "rero" in mef_record
    assert actions == {
        "069774331": {
            "MEF": {mef_pid: Action.DISCARD, mef_pid_new: Action.UPDATE},
            "action": Action.NOT_ONLINE,
            "source": "idref",
        },
        "12391664X": {
            "MEF": {
                mef_pid: Action.DISCARD,
                str(int(mef_pid) + 2): Action.DISCARD,
                mef_pid_new: Action.UPDATE,
            },
            "action": Action.NOT_ONLINE,
            "source": "gnd",
        },
        "A023655346": {
            "MEF": {mef_pid: Action.DISCARD, mef_pid_new: Action.UPDATE},
            "action": Action.NOT_ONLINE,
            "source": "rero",
        },
        "AXXXXXXXXX": {
            "MEF": {
                mef_pid_new: Action.DELETE,
                str(int(mef_pid_new) + 1): Action.CREATE,
            },
            "action": Action.DISCARD,
            "source": "rero",
        },
    }
    assert AgentMefRecord.count() == 5
    info = monitor.check_mef()
    assert info == {
        "aggnd": {"db": 1, "index": "aggnd", "mef": 1, "mef-db": 0},
        "agrero": {"db": 2, "index": "agrero", "mef": 2, "mef-db": 0},
        "aidref": {"db": 1, "index": "aidref", "mef": 1, "mef-db": 0},
        "cidref": {"db": 0, "index": "cidref", "mef": 0, "mef-db": 0},
        "cognd": {"db": 0, "index": "cognd", "mef": 0, "mef-db": 0},
        "corero": {"db": 0, "index": "corero", "mef": 0, "mef-db": 0},
        "pidref": {"db": 0, "index": "pidref", "mef": 0, "mef-db": 0},
        "plgnd": {"db": 0, "index": "plgnd", "mef": 0, "mef-db": 0},
    }

    # delete VIAF
    rec = AgentViafRecord.get_record_by_pid(agent_viaf_record.get("pid"))
    _, action, mef_actions = rec.delete(dbcommit=True, delindex=True)
    assert action == Action.DELETE

    # {'1': {'viaf': {'66739143': Action.DELETE}},
    #  '4': {'gnd': {'12391664X': Action.DELETE},
    #        'idref': {'069774331': Action.UPDATE},
    #        'rero': {'A023655346': Action.DELETE},
    #        'viaf': {'66739143': Action.DELETE}},
    #  '6': {'gnd': {'12391664X': Action.CREATE}},
    #  '7': {'rero': {'A023655346': Action.CREATE}}}

    assert mef_actions[mef_pid] == {"viaf": {agent_viaf_record.pid: Action.DELETE}}
    assert mef_actions[mef_pid_new]["viaf"] == {agent_viaf_record.pid: Action.DELETE}

    mef_record = AgentMefRecord.get_record_by_pid(mef_pid_new)
    assert "idref" in mef_record
    assert "gnd" not in mef_record
    assert "rero" not in mef_record
    assert "viaf_pid" not in mef_record

    info = monitor.check_mef()
    assert info == {
        "aggnd": {"db": 1, "index": "aggnd", "mef": 1, "mef-db": 0},
        "agrero": {"db": 2, "index": "agrero", "mef": 2, "mef-db": 0},
        "aidref": {"db": 1, "index": "aidref", "mef": 1, "mef-db": 0},
        "cidref": {"db": 0, "index": "cidref", "mef": 0, "mef-db": 0},
        "cognd": {"db": 0, "index": "cognd", "mef": 0, "mef-db": 0},
        "corero": {"db": 0, "index": "corero", "mef": 0, "mef-db": 0},
        "pidref": {"db": 0, "index": "pidref", "mef": 0, "mef-db": 0},
        "plgnd": {"db": 0, "index": "plgnd", "mef": 0, "mef-db": 0},
    }


@mock.patch("requests.Session.get")
def test_create_mef_and_agents_online(
    mock_session_get, app, aggnd_oai_139205527, script_info
):
    """Test online agent creation from a mocked GND response."""
    # We need OAI harvest informations for the online functions.
    runner = CliRunner()
    oaisources = os.path.join(os.path.dirname(__file__), "../../data/oaisources.yml")
    res = runner.invoke(init_oai_harvest_config, [oaisources], obj=script_info)
    assert res.output.strip().split("\n") == [
        "Add OAIHarvestConfig: agents.gnd https://services.dnb.de/oai/repository Added",
        "Add OAIHarvestConfig: agents.idref https://www.idref.fr/OAI/oai.jsp Added",
        "Add OAIHarvestConfig: concepts.idref https://www.idref.fr/OAI/oai.jsp Added",
        "Add OAIHarvestConfig: places.idref https://www.idref.fr/OAI/oai.jsp Added",
    ]
    viaf_record = AgentViafRecord.create(
        data={
            "$schema": "https://mef.rero.ch/schemas/viaf/viaf-v0.0.1.json",
            "pid": "VIAF_ONLINE_CREATE",
            "gnd_pid": "139205527",
        },
        dbcommit=True,
        reindex=True,
    )

    mock_session_get.return_value = mock_response(content=aggnd_oai_139205527)

    actions = viaf_record.create_mef_and_agents(
        dbcommit=True, reindex=True, online=["aggnd"], verbose=True
    )
    mef_pid = AgentMefRecord.get_mef(
        entity_pid=viaf_record.pid,
        entity_name=viaf_record.name,
        pid_only=True,
    )[0]

    assert actions["139205527"] == {
        "MEF": {mef_pid: Action.CREATE},
        "action": Action.CREATE,
        "source": "gnd",
    }


@mock.patch("requests.Session.get")
def test_handle_redirect(mock_get, app, agent_viaf_online_response):
    """Test VIAF redirect handling (cluster merge)."""
    # Create a proper VIAF record with persistent identifier
    old_pid = "12345678"
    viaf_data = {
        "$schema": "https://mef.rero.ch/schemas/viaf/viaf-v0.0.1.json",
        "pid": old_pid,
        "gnd_pid": "12391664X",
        "idref_pid": "069774331",
    }
    agent_viaf_record = AgentViafRecord.create(
        data=viaf_data, dbcommit=True, reindex=True
    )
    new_pid = "999999999"

    # Mock the target VIAF record online data
    target_data = deepcopy(agent_viaf_online_response)
    target_data["viafID"] = new_pid
    mock_get.return_value = mock_response(json_data=target_data)

    # Call handle_redirect
    new_record, action, redirect_info = agent_viaf_record.handle_redirect(
        redirect_to_pid=new_pid,
        dbcommit=True,
        reindex=True,
    )

    # Verify the redirect was handled correctly
    assert action == Action.REDIRECT
    assert redirect_info == {"from": old_pid, "to": new_pid}
    assert new_record.pid == new_pid

    # Verify old record was deleted
    assert AgentViafRecord.get_record_by_pid(old_pid) is None

    # Verify new record exists
    assert AgentViafRecord.get_record_by_pid(new_pid) is not None


@mock.patch("requests.Session.get")
def test_handle_redirect_target_not_found(mock_get, app):
    """Test VIAF redirect when target is not found."""
    # Create a proper VIAF record
    old_pid = "12345678"
    viaf_data = {
        "$schema": "https://mef.rero.ch/schemas/viaf/viaf-v0.0.1.json",
        "pid": old_pid,
        "gnd_pid": "12391664X",
    }
    agent_viaf_record = AgentViafRecord.create(
        data=viaf_data, dbcommit=True, reindex=True
    )
    old_pid = agent_viaf_record.pid
    new_pid = "999999999"

    # Mock response without viafID (target not found)
    mock_get.return_value = mock_response(json_data={"sources": {}})
    # Call handle_redirect
    new_record, action, redirect_info = agent_viaf_record.handle_redirect(
        redirect_to_pid=new_pid,
        dbcommit=True,
        reindex=True,
    )

    # Verify error handling
    assert action == Action.ERROR
    assert redirect_info == {"from": old_pid, "to": new_pid}
    assert new_record is None


@mock.patch("requests.Session.get")
def test_get_online_with_redirect(mock_get, app, agent_viaf_online_response):
    """Test get_online_record with redirect detection."""
    old_pid = "12345"
    new_pid = "67890"

    # Mock response with different PID (redirect)
    redirected_data = deepcopy(agent_viaf_online_response)
    redirected_data["viafID"] = new_pid
    mock_get.return_value = mock_response(json_data=redirected_data)

    data, msg = AgentViafRecord.get_online_record("VIAF", old_pid)

    # Verify redirect was detected
    assert data is None
    assert "REDIRECT" in msg
    assert new_pid in msg


@mock.patch("requests.Session.get")
def test_update_online_handles_redirect(
    mock_get, app, agent_viaf_record, agent_viaf_online_response
):
    """Test update_online reconciles merged VIAF clusters via handle_redirect."""
    viaf_record = AgentViafRecord.get_record_by_pid(agent_viaf_record.pid)
    if viaf_record is None:
        viaf_record = AgentViafRecord.create(
            data=dict(agent_viaf_record),
            dbcommit=True,
            reindex=True,
        )

    old_pid = viaf_record.pid
    new_pid = "999999999"

    redirected_data = deepcopy(agent_viaf_online_response)
    redirected_data["viafID"] = new_pid
    mock_get.return_value = mock_response(json_data=redirected_data)

    new_record, action = viaf_record.update_online(
        dbcommit=True,
        reindex=True,
    )

    assert action == Action.REDIRECT
    assert new_record.pid == new_pid
    assert AgentViafRecord.get_record_by_pid(old_pid) is None
    assert AgentViafRecord.get_record_by_pid(new_pid) is not None


@mock.patch("requests.Session.get")
def test_handle_redirect_chained(mock_get, app):
    """Test handle_redirect with chained redirect (error case)."""
    # Create a VIAF record
    old_pid = "11111111"
    viaf_data = {
        "$schema": "https://mef.rero.ch/schemas/viaf/viaf-v0.0.1.json",
        "pid": old_pid,
        "gnd_pid": "12391664X",
    }
    agent_viaf_record = AgentViafRecord.create(
        data=viaf_data, dbcommit=True, reindex=True
    )
    new_pid = "22222222"

    # Mock response with chained redirect (redirect_from still present)
    chained_data = {
        "viafID": "33333333",
        "redirect_from": new_pid,
        "sources": {},
    }
    mock_get.return_value = mock_response(json_data=chained_data)

    # Call handle_redirect - should return ERROR for chained redirect
    new_record, action, redirect_info = agent_viaf_record.handle_redirect(
        redirect_to_pid=new_pid,
        dbcommit=True,
        reindex=True,
    )

    # Verify error handling for chained redirect
    assert action == Action.ERROR
    assert new_record is None


@mock.patch("requests.Session.get")
def test_get_online_other_source(mock_get, app, agent_viaf_online_response):
    """Test get_online_record with non-VIAF source code."""
    pid = "076515788"

    mock_get.return_value = mock_response(json_data=agent_viaf_online_response)

    # Test with SUDOC source
    data, msg = AgentViafRecord.get_online_record("SUDOC", pid)

    assert data is not None
    assert "idref_pid" in data
    assert msg is not None


@mock.patch("requests.Session.get")
@mock.patch("rero_mef.agents.viaf.api.click.echo")
@mock.patch("rero_mef.agents.viaf.api._sleep_with_countdown")
def test_get_online_rate_limit_retry_after_capped(
    mock_wait, mock_echo, mock_get, app, agent_viaf_online_response
):
    """Cap Retry-After to RERO_MEF_VIAF_RETRY_AFTER_MAX and retry successfully."""
    old_delay = app.config.get("RERO_MEF_VIAF_REQUEST_DELAY")
    old_max = app.config.get("RERO_MEF_VIAF_RETRY_AFTER_MAX")
    app.config["RERO_MEF_VIAF_REQUEST_DELAY"] = 0
    app.config["RERO_MEF_VIAF_RETRY_AFTER_MAX"] = 60

    try:
        rate_limited = mock_response(status=429)
        rate_limited.headers = {"Retry-After": "9999"}
        success = mock_response(json_data=agent_viaf_online_response)
        mock_get.side_effect = [rate_limited, success]

        data, msg = AgentViafRecord.get_online_record("SUDOC", "076515788")

        assert data is not None
        assert "idref_pid" in data
        assert "OK" in msg
        echo_call = mock_echo.call_args[0][0]
        assert "capped to 60s" in echo_call
        mock_wait.assert_called_once_with(60)
    finally:
        app.config["RERO_MEF_VIAF_REQUEST_DELAY"] = old_delay
        app.config["RERO_MEF_VIAF_RETRY_AFTER_MAX"] = old_max


@mock.patch("requests.Session.get")
@mock.patch("rero_mef.agents.viaf.api.click.echo")
@mock.patch("rero_mef.agents.viaf.api._sleep_with_countdown")
def test_get_online_rate_limit_without_header_uses_default(
    mock_wait, mock_echo, mock_get, app
):
    """Use the default wait and raise on repeated 429 responses."""
    old_delay = app.config.get("RERO_MEF_VIAF_REQUEST_DELAY")
    old_default = app.config.get("RERO_MEF_VIAF_RETRY_AFTER_DEFAULT")
    app.config["RERO_MEF_VIAF_REQUEST_DELAY"] = 0
    app.config["RERO_MEF_VIAF_RETRY_AFTER_DEFAULT"] = 3

    try:
        rate_limited = mock_response(status=429)
        rate_limited.headers = {}
        mock_get.side_effect = [rate_limited, rate_limited]

        with pytest.raises(RetryableVIAFError, match=r"RATE LIMITED \(429\)"):
            AgentViafRecord.get_online_record("SUDOC", "076515788")

        mock_echo.assert_called_once()
        mock_wait.assert_called_once_with(3)
    finally:
        app.config["RERO_MEF_VIAF_REQUEST_DELAY"] = old_delay
        app.config["RERO_MEF_VIAF_RETRY_AFTER_DEFAULT"] = old_default


def test_handle_redirect_retryable_target_failure_does_not_delete_old_record(app):
    """Test transient target fetch failures do not delete the old VIAF record."""
    old_pid = "12345679"
    new_pid = "999999997"
    viaf_record = AgentViafRecord.create(
        data={
            "$schema": "https://mef.rero.ch/schemas/viaf/viaf-v0.0.1.json",
            "pid": old_pid,
            "gnd_pid": "12391664X",
        },
        dbcommit=True,
        reindex=True,
    )

    with mock.patch.object(
        AgentViafRecord,
        "get_online_record",
        side_effect=RetryableVIAFError("temporary failure"),
    ):
        new_record, action, redirect_info = viaf_record.handle_redirect(
            redirect_to_pid=new_pid,
            dbcommit=True,
            reindex=True,
            delete_if_not_found=True,
        )

    assert new_record is None
    assert action == Action.ERROR
    assert redirect_info == {"from": old_pid, "to": new_pid}
    assert AgentViafRecord.get_record_by_pid(old_pid) is not None


@mock.patch("requests.Session.get")
def test_handle_redirect_create_or_update_exception(
    mock_get, app, agent_viaf_online_response
):
    """Test handle_redirect when create_or_update raises an exception."""
    old_pid = "11111112"
    new_pid = "99999998"

    viaf_data = {
        "$schema": "https://mef.rero.ch/schemas/viaf/viaf-v0.0.1.json",
        "pid": old_pid,
    }
    viaf_record = AgentViafRecord.create(data=viaf_data, dbcommit=True, reindex=True)

    target_data = deepcopy(agent_viaf_online_response)
    target_data["viafID"] = new_pid
    mock_get.return_value = mock_response(json_data=target_data)

    with mock.patch.object(
        AgentViafRecord, "create_or_update", side_effect=Exception("DB error")
    ):
        new_record, action, redirect_info = viaf_record.handle_redirect(
            redirect_to_pid=new_pid, dbcommit=True, reindex=True
        )

    assert action == Action.ERROR
    assert new_record is None
    assert redirect_info == {"from": old_pid, "to": new_pid}
