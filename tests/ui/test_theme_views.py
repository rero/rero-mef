# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for UI theme views."""

from flask import url_for


def test_robots_txt(client):
    """robots.txt disallows all UI paths."""
    res = client.get("/robots.txt")
    assert res.status_code == 200
    assert res.content_type == "text/plain; charset=utf-8"
    body = res.get_data(as_text=True)
    assert "User-agent: *" in body
    assert "Disallow: /" in body
    assert "Disallow: /all" in body


def test_index(client):
    """Home page returns 200."""
    res = client.get(url_for("rero_mef.index"))
    assert res.status_code == 200


def test_all_mef_list(client):
    """All MEF list page returns 200."""
    res = client.get(url_for("rero_mef.all_mef_list"))
    assert res.status_code == 200


def test_linking(client):
    """Linking overview page returns 200 and contains all three entity sections."""
    res = client.get(url_for("rero_mef.linking"))
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "VIAF" in body
    assert "FRBNF" in body
    assert "redirect_from" in body


def test_agent_detail(client, agent_mef_record):
    """Detail page returns 200 for known PID and 404 for unknown."""
    res = client.get(f"/agents/{agent_mef_record.pid}")
    assert res.status_code == 200
    assert agent_mef_record.pid in res.get_data(as_text=True)
    assert client.get("/agents/UNKNOWN").status_code == 404


def test_agent_latest_redirect(client, agent_mef_gnd_redirect_record, agent_mef_record):
    """Latest route resolves the current source PID and redirects to the current MEF page."""
    res = client.get("/agents/latest/gnd:12391664X")
    assert res.status_code == 302
    assert f"/agents/{agent_mef_record.pid}" in res.headers["Location"]
    assert client.get("/agents/latest/gnd:UNKNOWN").status_code == 404


def test_agent_older_redirect(
    client, agent_mef_idref_redirect_record, agent_mef_record
):
    """Older route resolves the old IDREF source PID and redirects to the older MEF page."""
    res = client.get("/agents/older/idref:069774331")
    assert res.status_code == 302
    assert f"/agents/{agent_mef_record.pid}" in res.headers["Location"]
    assert client.get("/agents/older/idref:UNKNOWN").status_code == 404


def test_agent_detail_latest_button(
    client, agent_mef_gnd_redirect_record, agent_mef_record
):
    """Old GND record (redirect_to) shows Latest button on its detail page."""
    res = client.get(f"/agents/{agent_mef_gnd_redirect_record.pid}")
    assert res.status_code == 200
    assert "mef-latest-link" in res.get_data(as_text=True)


def test_agent_detail_older_button_idref(
    client, agent_mef_idref_redirect_record, agent_mef_record
):
    """Canonical IDREF record (redirect_from) shows Older button on its detail page."""
    res = client.get(f"/agents/{agent_mef_idref_redirect_record.pid}")
    assert res.status_code == 200
    assert "mef-older-link" in res.get_data(as_text=True)


def test_agent_detail_older_button_gnd_reverse(
    client, agent_mef_record, agent_mef_gnd_redirect_record
):
    """Current GND record shows Older button via reverse redirect_to lookup."""
    res = client.get(f"/agents/{agent_mef_record.pid}")
    assert res.status_code == 200
    assert "mef-older-link" in res.get_data(as_text=True)


def test_agent_detail_crosstype_redirect(client, agent_mef_crosstype_redirect_record):
    """MEF record whose GND source (bf:Organisation) redirects to a bf:Person shows the type-conflict alert.

    The redirect target (12391664X) exists as an agent MEF record, so the relation_pid link
    is a normal internal link (no mef-conflict-link class).  The alert fires because the
    source and target have different bf:types.
    """
    res = client.get(f"/agents/{agent_mef_crosstype_redirect_record.pid}")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "mef-type-conflict-alert" in body
    assert "mef-conflict-link" not in body
