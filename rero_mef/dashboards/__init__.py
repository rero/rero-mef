# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""OpenSearch Dashboards index patterns and the MEF dashboard."""

import json
import time
from importlib.resources import files

import requests

DASHBOARD_ID = "mef-complete"
NDJSON = files(__name__) / "mef-dashboard.ndjson"
HEADERS = {"osd-xsrf": "true"}
#: Dashboards drops every field starting with `_` that is not a meta field: the growth charts aggregate on the
#: records' `_created` and `_updated`, the concept panel on `_association_level`.
META_FIELDS = ["_source", "_id", "_type", "_index", "_score", "_created", "_updated", "_association_level"]
#: One index pattern per index, for Discover. The dashboard brings its own.
INDEX_PATTERNS = {
    "agents_gnd": "agents_gnd*",
    "agents_idref": "agents_idref*",
    "agents_rero": "agents_rero*",
    "viaf": "viaf*",
    "agents_mef": "mef*",
    "concepts_gnd": "concepts_gnd*",
    "concepts_idref": "concepts_idref*",
    "concepts_rero": "concepts_rero*",
    "concepts_mef": "concepts_mef*",
    "places_gnd": "places_gnd*",
    "places_idref": "places_idref*",
    "places_mef": "places_mef*",
}


def dashboards_running(url, timeout=2):
    """Tell whether OpenSearch Dashboards answers at `url`.

    :param url: Dashboards base URL.
    :param timeout: Seconds to wait for the answer.
    :returns: True when Dashboards answers.
    """
    try:
        return requests.get(f"{url}/api/status", timeout=timeout).ok
    except requests.RequestException:
        return False


def wait_for_dashboards(url, attempts=30, delay=2):
    """Wait until OpenSearch Dashboards answers at `url`.

    :param url: Dashboards base URL.
    :param attempts: Number of tries.
    :param delay: Seconds between two tries.
    :returns: True when Dashboards answered before the tries ran out.
    """
    for attempt in range(attempts):
        if dashboards_running(url):
            return True
        if attempt < attempts - 1:
            time.sleep(delay)
    return False


def install_dashboard(url):
    """Set the meta fields, register the index patterns and import the MEF dashboard.

    :param url: Dashboards base URL.
    :returns: Number of imported objects.
    :raises requests.HTTPError: When Dashboards refuses a request.
    """
    requests.post(
        f"{url}/api/opensearch-dashboards/settings",
        headers=HEADERS,
        json={"changes": {"metaFields": META_FIELDS}},
        timeout=30,
    ).raise_for_status()
    for pattern_id, title in INDEX_PATTERNS.items():
        response = requests.post(
            f"{url}/api/saved_objects/index-pattern/{pattern_id}",
            headers=HEADERS,
            json={"attributes": {"title": title, "timeFieldName": ""}},
            timeout=30,
        )
        # 409: registered by an earlier run
        if response.status_code != 409:
            response.raise_for_status()
    with NDJSON.open("rb") as ndjson:
        response = requests.post(
            f"{url}/api/saved_objects/_import",
            params={"overwrite": "true"},
            headers=HEADERS,
            files={"file": (NDJSON.name, ndjson, "application/ndjson")},
            timeout=60,
        )
    response.raise_for_status()
    return response.json()["successCount"]


def export_dashboard(url, path=NDJSON):
    """Write the MEF dashboard as edited in Dashboards, with everything it references, to `path`.

    :param url: Dashboards base URL.
    :param path: NDJSON file to write.
    :returns: Number of exported objects.
    :raises requests.HTTPError: When Dashboards refuses the export.
    """
    response = requests.post(
        f"{url}/api/saved_objects/_export",
        headers=HEADERS,
        json={"objects": [{"type": "dashboard", "id": DASHBOARD_ID}], "includeReferencesDeep": True},
        timeout=60,
    )
    response.raise_for_status()
    # The last line only counts the exported objects.
    lines = [line for line in response.text.splitlines() if line and "exportedCount" not in json.loads(line)]
    path.write_text("\n".join(lines))
    return len(lines)
