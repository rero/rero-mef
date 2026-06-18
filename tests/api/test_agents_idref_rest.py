# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test REST API IDREF."""

import json

from flask import url_for


def test_view_agents_idref(client, agent_idref_record):
    """Test redirect IDREF."""
    pid = agent_idref_record.get("pid")
    url = url_for("invenio_records_rest.aidref_list")
    res = client.get(url)
    assert res.status_code == 200
    assert json.loads(res.get_data(as_text=True))["aggregations"] == {
        "type": {
            "buckets": [{"doc_count": 1, "key": "bf:Person"}],
            "doc_count_error_upper_bound": 0,
            "sum_other_doc_count": 0,
        },
        "deleted": {"doc_count": 0},
        "identifiedBy_source": {
            "buckets": [],
            "doc_count_error_upper_bound": 0,
            "sum_other_doc_count": 0,
        },
    }

    url = url_for("invenio_records_rest.aidref_item", pid_value=pid)
    res = client.get(url)
    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    assert data.get("id") == pid
    assert data.get("metadata", {}).get("pid") == pid

    url = url_for("invenio_records_rest.aidref_item", pid_value="WRONG")
    res = client.get(url, follow_redirects=True)
    assert res.status_code == 404
    assert json.loads(res.get_data(as_text=True)) == {
        "status": 404,
        "message": "PID does not exist.",
    }
