# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for UI theme views."""

from flask import url_for

from rero_mef.agents import AgentGndRecord, AgentIdrefRecord, AgentMefRecord
from rero_mef.utils import build_ref_string

from ..utils import create_record


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


def test_agent_older_redirect(client, agent_mef_idref_redirect_record, agent_mef_record):
    """Older route resolves the old IDREF source PID and redirects to the older MEF page."""
    res = client.get("/agents/older/idref:069774331")
    assert res.status_code == 302
    assert f"/agents/{agent_mef_record.pid}" in res.headers["Location"]
    assert client.get("/agents/older/idref:UNKNOWN").status_code == 404


def test_agent_detail_latest_button(client, agent_mef_gnd_redirect_record, agent_mef_record):
    """Old GND record (redirect_to) shows Latest button on its detail page."""
    res = client.get(f"/agents/{agent_mef_gnd_redirect_record.pid}")
    assert res.status_code == 200
    assert "mef-latest-link" in res.get_data(as_text=True)


def test_agent_detail_older_button_idref(client, agent_mef_idref_redirect_record, agent_mef_record):
    """Canonical IDREF record (redirect_from) shows Older button on its detail page."""
    res = client.get(f"/agents/{agent_mef_idref_redirect_record.pid}")
    assert res.status_code == 200
    assert "mef-older-link" in res.get_data(as_text=True)


def test_agent_detail_older_button_gnd_reverse(client, agent_mef_record, agent_mef_gnd_redirect_record):
    """Current GND record shows Older button via reverse redirect_to lookup."""
    res = client.get(f"/agents/{agent_mef_record.pid}")
    assert res.status_code == 200
    assert "mef-older-link" in res.get_data(as_text=True)


def test_agent_detail_latest_button_idref_reverse(client, agent_mef_idref_redirect_record, agent_mef_record):
    """Old IDREF record shows Latest button via reverse redirect_from lookup."""
    res = client.get(f"/agents/{agent_mef_record.pid}")
    assert res.status_code == 200
    assert "mef-latest-link" in res.get_data(as_text=True)


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


def test_agent_detail_conflicting_latest_targets(app, client):
    """GND and IDREF redirecting to two different records both show up as Latest links.

    Self-contained fixtures (unique pids) rather than the shared module-scoped
    ones, since this needs a record whose GND *and* IDREF sources each point to
    a different successor -- none of the existing shared fixtures combine both
    at once, and mutating them would affect other tests in this module.
    """
    gnd_old = create_record(
        AgentGndRecord,
        {
            "pid": "9990001",
            "type": "bf:Person",
            "authorized_access_point": "Conflict GND Old",
            "relation_pid": {"type": "redirect_to", "value": "9990002"},
            "$schema": "https://mef.rero.ch/schemas/agents_gnd/gnd-agent-v0.0.1.json",
        },
    )
    gnd_new = create_record(
        AgentGndRecord,
        {
            "pid": "9990002",
            "type": "bf:Person",
            "authorized_access_point": "Conflict GND New",
            "$schema": "https://mef.rero.ch/schemas/agents_gnd/gnd-agent-v0.0.1.json",
        },
    )
    idref_old = create_record(
        AgentIdrefRecord,
        {
            "pid": "9990003",
            "type": "bf:Person",
            "authorized_access_point": "Conflict IdRef Old",
            "$schema": "https://mef.rero.ch/schemas/agents_idref/idref-agent-v0.0.1.json",
        },
    )
    idref_new = create_record(
        AgentIdrefRecord,
        {
            "pid": "9990004",
            "type": "bf:Person",
            "authorized_access_point": "Conflict IdRef New",
            "relation_pid": {"type": "redirect_from", "value": "9990003"},
            "$schema": "https://mef.rero.ch/schemas/agents_idref/idref-agent-v0.0.1.json",
        },
    )
    mef_old = create_record(
        AgentMefRecord,
        {
            "gnd": {"$ref": build_ref_string(entity_type="agents", entity_name="gnd", entity_pid=gnd_old.pid)},
            "idref": {"$ref": build_ref_string(entity_type="agents", entity_name="idref", entity_pid=idref_old.pid)},
            "$schema": "https://mef.rero.ch/schemas/mef/mef-v0.0.1.json",
        },
    )
    mef_gnd_new = create_record(
        AgentMefRecord,
        {
            "gnd": {"$ref": build_ref_string(entity_type="agents", entity_name="gnd", entity_pid=gnd_new.pid)},
            "$schema": "https://mef.rero.ch/schemas/mef/mef-v0.0.1.json",
        },
    )
    mef_idref_new = create_record(
        AgentMefRecord,
        {
            "idref": {"$ref": build_ref_string(entity_type="agents", entity_name="idref", entity_pid=idref_new.pid)},
            "$schema": "https://mef.rero.ch/schemas/mef/mef-v0.0.1.json",
        },
    )

    res = client.get(f"/agents/{mef_old.pid}")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert body.count("mef-latest-link") == 2
    assert f"/agents/latest/gnd:{gnd_new.pid}" in body
    assert f"/agents/latest/idref:{idref_new.pid}" in body
    assert "Latest (GND)" in body
    assert "Latest (IDREF)" in body

    # each redirect route resolves to the correct, distinct MEF record
    res = client.get(f"/agents/latest/gnd:{gnd_new.pid}", follow_redirects=True)
    assert res.status_code == 200
    assert res.request.path == f"/agents/{mef_gnd_new.pid}"
    res = client.get(f"/agents/latest/idref:{idref_new.pid}", follow_redirects=True)
    assert res.status_code == 200
    assert res.request.path == f"/agents/{mef_idref_new.pid}"
