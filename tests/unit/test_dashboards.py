# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test the OpenSearch Dashboards install and export of the MEF dashboard."""

import json
from unittest import mock

import pytest
import requests

from rero_mef import dashboards
from rero_mef.dashboards import (
    META_FIELDS,
    NDJSON,
    dashboards_running,
    export_dashboard,
    install_dashboard,
    wait_for_dashboards,
)

URL = "http://dashboards:5601"


def response(status=200, payload=None, text=""):
    res = requests.Response()
    res.status_code = status
    res._content = json.dumps(payload).encode() if payload is not None else text.encode()
    return res


def test_bundled_dashboard_is_consistent():
    """Every panel, visualization and field the dashboard needs is in the NDJSON."""
    objects = {obj["id"]: obj for obj in map(json.loads, NDJSON.read_text().splitlines())}
    dashboard = objects["mef-complete"]
    panels = json.loads(dashboard["attributes"]["panelsJSON"])
    references = {ref["name"]: ref["id"] for ref in dashboard["references"]}
    assert {panel["panelRefName"] for panel in panels} == set(references)
    fields = {
        obj["id"]: {field["name"] for field in json.loads(obj["attributes"]["fields"])}
        for obj in objects.values()
        if obj["type"] == "index-pattern"
    }
    for vis_id in references.values():
        vis = objects[vis_id]
        pattern = vis["references"][0]["id"]
        for agg in json.loads(vis["attributes"]["visState"])["aggs"]:
            if field := agg["params"].get("field"):
                assert field in fields[pattern], f"{vis_id}: {field}"
                # Dashboards drops the `_` fields that are not meta fields
                assert not field.startswith("_") or field in META_FIELDS, f"{vis_id}: {field}"


@pytest.mark.parametrize(
    ("side_effect", "expected"),
    [(response(200), True), (response(503), False), (requests.ConnectionError(), False)],
)
def test_dashboards_running(side_effect, expected):
    """Only a successful status answer counts as running."""
    with mock.patch.object(dashboards.requests, "get", side_effect=[side_effect]):
        assert dashboards_running(URL) is expected


def test_wait_for_dashboards():
    """Waiting stops at the first answer, and gives up after the last try."""
    with (
        mock.patch.object(dashboards, "dashboards_running", side_effect=[False, True]) as running,
        mock.patch.object(dashboards.time, "sleep") as sleep,
    ):
        assert wait_for_dashboards(URL, attempts=3)
    assert running.call_count == 2
    sleep.assert_called_once()
    with (
        mock.patch.object(dashboards, "dashboards_running", return_value=False),
        mock.patch.object(dashboards.time, "sleep") as sleep,
    ):
        assert not wait_for_dashboards(URL, attempts=3)
    assert sleep.call_count == 2


def test_install_dashboard():
    """The meta fields come first, an index pattern already there is accepted, the NDJSON is imported."""
    patterns = [response(409 if pattern_id == "viaf" else 200) for pattern_id in dashboards.INDEX_PATTERNS]
    answers = [response(200), *patterns, response(200, {"success": True, "successCount": 38})]
    with mock.patch.object(dashboards.requests, "post", side_effect=answers) as post:
        assert install_dashboard(URL) == 38
    settings, *registered, imported = post.call_args_list
    assert settings.args == (f"{URL}/api/opensearch-dashboards/settings",)
    assert settings.kwargs["json"] == {"changes": {"metaFields": META_FIELDS}}
    assert len(registered) == len(dashboards.INDEX_PATTERNS)
    assert imported.args == (f"{URL}/api/saved_objects/_import",)
    assert imported.kwargs["params"] == {"overwrite": "true"}


def test_install_dashboard_refused():
    """A refused index pattern stops the install before the import."""
    with (
        mock.patch.object(dashboards.requests, "post", side_effect=[response(200), response(400)]) as post,
        pytest.raises(requests.HTTPError),
    ):
        install_dashboard(URL)
    assert post.call_count == 2


def test_export_dashboard(tmp_path):
    """The export keeps the objects and drops the closing count."""
    lines = [{"type": "index-pattern", "id": "mef-all"}, {"type": "dashboard", "id": "mef-complete"}]
    text = "\n".join(json.dumps(line) for line in [*lines, {"exportedCount": 2, "missingRefCount": 0}])
    path = tmp_path / "mef-dashboard.ndjson"
    with mock.patch.object(dashboards.requests, "post", return_value=response(200, text=text)) as post:
        assert export_dashboard(URL, path) == 2
    assert post.call_args.kwargs["json"]["objects"] == [{"type": "dashboard", "id": "mef-complete"}]
    assert [json.loads(line) for line in path.read_text().splitlines()] == lines
