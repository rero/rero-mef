# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test REST API MEF."""

import json
from datetime import UTC, datetime, timedelta

from flask import url_for

from rero_mef.places import PlaceMefRecord

from ..utils import postdata


def test_view_places_mef(
    client, place_mef_idref_redirect_record, place_idref_redirect_record
):
    """Test places MEF."""
    pid = place_mef_idref_redirect_record.get("pid")
    url = url_for("invenio_records_rest.pidref_list")
    res = client.get(url)
    assert res.status_code == 200
    json_data = json.loads(res.get_data(as_text=True))

    url = url_for("invenio_records_rest.plmef_list")
    res = client.get(url)
    assert res.status_code == 200
    json_data = json.loads(res.get_data(as_text=True))
    assert json_data["hits"]["total"] == 1
    aggs = json_data["aggregations"]
    aggs.pop("creation_date", None)
    aggs.pop("update_date", None)
    assert aggs == {
        "authorized_access_point": {
            "buckets": [],
            "doc_count_error_upper_bound": 0,
            "sum_other_doc_count": 0,
        },
        "deleted": {"doc_count": 0},
        "source": {
            "buckets": [{"doc_count": 1, "key": "idref"}],
            "doc_count_error_upper_bound": 0,
            "sum_other_doc_count": 0,
        },
        "type": {
            "buckets": [{"doc_count": 1, "key": "bf:Place"}],
            "doc_count_error_upper_bound": 0,
            "sum_other_doc_count": 0,
        },
    }
    url = url_for("invenio_records_rest.plmef_item", pid_value=pid)
    res = client.get(url)
    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    assert data.get("id") == pid
    assert data.get("metadata", {}).get("pid") == pid

    url = url_for("invenio_records_rest.plmef_item", pid_value="WRONG")
    res = client.get(url, follow_redirects=True)
    assert res.status_code == 404
    assert json.loads(res.get_data(as_text=True)) == {
        "status": 404,
        "message": "PID does not exist.",
    }


def test_places_mef_get_latest(
    client,
    place_mef_idref_record,
    place_idref_record,
    place_mef_idref_redirect_record,
    place_idref_redirect_record,
):
    """Test places MEF get latest."""
    mef_data = place_mef_idref_redirect_record.add_information(resolve=True)
    # New IdRef record is old IdRef record
    data = PlaceMefRecord.get_latest(
        pid_type="idref", pid=place_idref_redirect_record.pid
    )
    data.pop("_created")
    data.pop("_updated")
    assert data == mef_data

    # New IdRef record is one redirect IdRef record
    # New IdRef record is one redirect IdRef record
    data = PlaceMefRecord.get_latest(pid_type="idref", pid=place_idref_record.pid)
    data.pop("_created")
    data.pop("_updated")
    assert data == mef_data

    # test REST API
    url = url_for(
        "api_blueprint.place_mef_get_latest",
        pid_type="idref",
        pid=place_idref_record.pid,
    )
    res = client.get(url)
    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    data.pop("_created")
    data.pop("_updated")
    assert data == mef_data


def test_places_mef_get_updated(
    client,
    place_mef_idref_record,
    place_idref_record,
    place_mef_idref_redirect_record,
    place_idref_redirect_record,
):
    """Test places MEF get updated."""
    # New IdRef record is one redirect IdRef record
    res, data = postdata(client, "api_blueprint.place_mef_get_updated", {})
    assert res.status_code == 200
    pids = sorted([rec.get("pid") for rec in data])
    assert pids == ["1", "2"]

    res, data = postdata(client, "api_blueprint.place_mef_get_updated", {"pids": ["2"]})
    assert res.status_code == 200
    pids = sorted([rec.get("pid") for rec in data])
    assert pids == ["2"]

    res, data = postdata(
        client, "api_blueprint.place_mef_get_updated", {"from_date": "2022-02-02"}
    )
    assert res.status_code == 200
    pids = sorted([rec.get("pid") for rec in data])
    assert pids == ["1", "2"]

    date = datetime.now(UTC) + timedelta(days=1)
    res, data = postdata(
        client, "api_blueprint.place_mef_get_updated", {"from_date": date.isoformat()}
    )
    assert res.status_code == 200
    pids = sorted([rec.get("pid") for rec in data])
    assert pids == []
