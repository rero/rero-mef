# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test REST API monitoring."""

from flask import url_for

from rero_mef.agents.idref.api import AgentIdrefRecord

from ..utils import create_and_login_monitoring_user, get_json


def test_monitoring_check_search_db_counts(app, client, agent_idref_data):
    """The shared monitoring links the MEF records missing in the index."""
    create_and_login_monitoring_user(app, client)
    AgentIdrefRecord.create(data=agent_idref_data, delete_pid=False, dbcommit=True, reindex=False)
    AgentIdrefRecord.flush_indexes()

    res = client.get(url_for("api_monitoring.check_search_db_counts", delay=0))
    assert res.status_code == 200
    data = get_json(res)
    assert data["data"] == {"status": "red"}
    assert data["errors"][0]["links"]["aidref"] == "http://localhost/monitoring/missing_pids/aidref"

    res = client.get(url_for("api_monitoring.missing_pids", doc_type="aidref", delay=0))
    assert res.status_code == 200
    assert get_json(res) == {
        "data": {"DB": [], "search": ["http://localhost/agents/idref/069774331"], "search duplicate": []}
    }


def test_monitoring_mef_counts(app, client):
    """The MEF counts are given to the monitoring role only."""
    res = client.get(url_for("mef_monitoring.mef_counts"))
    assert res.status_code == 401

    create_and_login_monitoring_user(app, client)
    res = client.get(url_for("mef_monitoring.mef_counts"))
    assert res.status_code == 200
    assert "data" in get_json(res)
