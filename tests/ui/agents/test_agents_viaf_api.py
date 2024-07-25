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

"""Test agents MEF api."""

import os
from copy import deepcopy

import mock
import pytest
from click.testing import CliRunner
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from utils import mock_response

from rero_mef.agents import (
    Action,
    AgentMefRecord,
    AgentReroRecord,
    AgentViafRecord,
    AgentViafSearch,
)
from rero_mef.cli import init_oai_harvest_config
from rero_mef.monitoring import Monitoring


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
        "http://www.viaf.org/viaf/sourceID/SUDOC|076515788/viaf.json | OK"
    )

    mock_get.return_value = mock_response(json_data=agent_viaf_online_response)
    data, msg = AgentViafRecord.get_online_record(
        "SUDOC", "076515788", rec_format="raw"
    )
    assert data == agent_viaf_online_response
    assert msg == (
        "VIAF get: 076515788       "
        "http://www.viaf.org/viaf/sourceID/SUDOC|076515788/viaf.json | OK"
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
            "MEF": {mef_pid: Action.UPTODATE},
            "action": Action.NOT_ONLINE,
            "source": "idref",
        },
        "12391664X": {
            "MEF": {mef_pid: Action.UPTODATE},
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
            "MEF": {mef_pid: Action.UPTODATE},
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
@mock.patch("requests.get")
def test_create_mef_and_agents_online(
    mock_get, mock_session_get, app, agent_viaf_record, script_info
):
    """Test create MEF and agents online."""
    # We need OAI harvest informations for the online functions.
    runner = CliRunner()
    oaisources = os.path.join(os.path.dirname(__file__), "../../data/oaisources.yml")
    res = runner.invoke(init_oai_harvest_config, [oaisources], obj=script_info)
    assert res.output.strip().split("\n") == [
        "Add OAIHarvestConfig: "
        "agents.gnd https://services.dnb.de/oai/repository Added",
        "Add OAIHarvestConfig: " "agents.idref https://www.idref.fr/OAI/oai.jsp Added",
        "Add OAIHarvestConfig: "
        "concepts.idref https://www.idref.fr/OAI/oai.jsp Added",
        "Add OAIHarvestConfig: " "places.idref https://www.idref.fr/OAI/oai.jsp Added",
    ]
    mock_get.return_value = mock_response(content="")
    mock_session_get.return_value = mock_response(content="")
    actions = agent_viaf_record.create_mef_and_agents(
        dbcommit=True, reindex=True, online=["aggnd", "aidref"], verbose=True
    )
    # TODO: 'action': Action.NOT_FOUND ????
    assert actions["069774331"] == {"action": Action.NOT_FOUND, "source": "idref"}
    assert actions["12391664X"] == {"action": Action.NOT_FOUND, "source": "gnd"}
