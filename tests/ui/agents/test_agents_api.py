# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test agents api."""

import os
from types import SimpleNamespace
from unittest import mock

from rero_mef.agents import (
    Action,
    AgentGndRecord,
    AgentIdrefRecord,
    AgentMefRecord,
    AgentReroRecord,
    AgentViafRecord,
)
from rero_mef.utils import export_json_records, number_records_in_file


class _FakeSearch:
    def __init__(self, hits):
        self._hits = hits
        self.params_calls = []
        self.scan_count = 0

    def params(self, **kwargs):
        self.params_calls.append(kwargs)
        return self

    def filter(self, *_args, **_kwargs):
        return self

    def exclude(self, *_args, **_kwargs):
        return self

    def source(self, *_args, **_kwargs):
        return self

    def scan(self):
        for hit in self._hits:
            self.scan_count += 1
            yield hit


class _FakeHit:
    def __init__(self, data, record_id):
        self._data = data
        self.meta = SimpleNamespace(id=record_id)

    def to_dict(self):
        return self._data


class _FakeRecord(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_calls = []

    def update(self, data, dbcommit=False, reindex=False):
        self.update_calls.append(
            {"data": dict(data), "dbcommit": dbcommit, "reindex": reindex}
        )
        return self


def test_create_agent_record_with_viaf_links(
    app, agent_viaf_data, agent_gnd_data, agent_rero_data, agent_idref_data, tmpdir
):
    """Test create agent record with VIAF links."""
    viaf_record, action = AgentViafRecord.create_or_update(
        agent_viaf_data, dbcommit=True, reindex=True
    )
    AgentViafRecord.flush_indexes()
    assert action == Action.CREATE
    assert viaf_record["pid"] == "66739143"
    assert viaf_record["gnd_pid"] == "12391664X"
    assert viaf_record["rero_pid"] == "A023655346"
    assert viaf_record["idref_pid"] == "069774331"
    assert len(viaf_record.get_entities_pids()) == 3
    assert viaf_record.get_entities_records() == []
    _, pids_viaf = viaf_record.get_missing_entity_pids("aidref")
    assert pids_viaf == ["66739143"]

    gnd_record, action = AgentGndRecord.create_or_update(
        data=agent_gnd_data, dbcommit=True, reindex=True
    )
    assert action == Action.CREATE
    assert gnd_record["pid"] == "12391664X"

    m_record, m_actions = gnd_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {"1": Action.CREATE}
    assert "md5" in m_record
    assert {k: v for k, v in m_record.items() if k != "md5"} == {
        "$schema": "https://mef.rero.ch/schemas/mef/mef-v0.0.1.json",
        "gnd": {"$ref": "https://mef.rero.ch/api/agents/gnd/12391664X"},
        "pid": "1",
        "type": "bf:Person",
        "viaf_pid": "66739143",
    }
    assert [
        {k: v for k, v in r.items() if k != "md5"}
        for r in viaf_record.get_entities_records()
    ] == [agent_gnd_data]
    assert viaf_record.get_viaf(m_record) == [viaf_record]
    assert viaf_record.get_viaf(gnd_record) == [viaf_record]
    pids_db, pids_viaf = viaf_record.get_missing_entity_pids("aggnd")
    assert pids_db == []
    assert pids_viaf == []

    rero_record, action = AgentReroRecord.create_or_update(
        data=agent_rero_data, dbcommit=True, reindex=True
    )
    assert action == Action.CREATE
    assert rero_record["pid"] == "A023655346"
    m_record, m_actions = rero_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {"1": Action.UPDATE}
    assert "md5" in m_record
    assert {k: v for k, v in m_record.items() if k != "md5"} == {
        "$schema": "https://mef.rero.ch/schemas/mef/mef-v0.0.1.json",
        "gnd": {"$ref": "https://mef.rero.ch/api/agents/gnd/12391664X"},
        "pid": "1",
        "rero": {"$ref": "https://mef.rero.ch/api/agents/rero/A023655346"},
        "type": "bf:Person",
        "viaf_pid": "66739143",
    }
    assert [
        {k: v for k, v in r.items() if k != "md5"}
        for r in viaf_record.get_entities_records()
    ] == [agent_gnd_data, agent_rero_data]

    idref_record, action = AgentIdrefRecord.create_or_update(
        data=agent_idref_data, dbcommit=True, reindex=True
    )
    assert action == Action.CREATE
    assert idref_record["pid"] == "069774331"
    m_record, m_actions = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {"1": Action.UPDATE}
    assert "md5" in m_record
    assert {k: v for k, v in m_record.items() if k != "md5"} == {
        "$schema": "https://mef.rero.ch/schemas/mef/mef-v0.0.1.json",
        "gnd": {"$ref": "https://mef.rero.ch/api/agents/gnd/12391664X"},
        "idref": {"$ref": "https://mef.rero.ch/api/agents/idref/069774331"},
        "pid": "1",
        "rero": {"$ref": "https://mef.rero.ch/api/agents/rero/A023655346"},
        "type": "bf:Person",
        "viaf_pid": "66739143",
    }
    assert [
        {k: v for k, v in r.items() if k != "md5"}
        for r in viaf_record.get_entities_records()
    ] == [
        agent_idref_data,
        agent_gnd_data,
        agent_rero_data,
    ]

    assert (
        m_record
        == AgentMefRecord.get_mef(
            entity_pid=idref_record.pid, entity_name=idref_record.name
        )[0]
    )
    assert (
        m_record.pid
        == AgentMefRecord.get_mef(
            entity_pid=gnd_record.pid, entity_name=gnd_record.name, pid_only=True
        )[0]
    )
    mef_rec_resolved = AgentMefRecord.get_mef(
        entity_pid=viaf_record.pid, entity_name=viaf_record.name
    )[0]
    assert m_record == mef_rec_resolved

    mef_rec_resolved = mef_rec_resolved.replace_refs()
    assert mef_rec_resolved.get("gnd").get("pid") == gnd_record.pid
    assert mef_rec_resolved.get("rero").get("pid") == rero_record.pid
    assert mef_rec_resolved.get("idref").get("pid") == idref_record.pid

    # Test JSON export.
    tmp_file_name = os.path.join(tmpdir, "mef.json")
    export_json_records(
        pids=AgentMefRecord.get_all_pids(),
        pid_type="mef",
        output_file_name=tmp_file_name,
    )
    assert number_records_in_file(tmp_file_name, "json") == 1
    assert "$schema" in open(tmp_file_name).read()
    export_json_records(
        pids=AgentMefRecord.get_all_pids(),
        pid_type="mef",
        output_file_name=tmp_file_name,
        schema=False,
    )
    assert number_records_in_file(tmp_file_name, "json") == 1
    assert "$schema" not in open(tmp_file_name).read()

    # Test update agent record with VIAF links.
    returned_record, action = AgentGndRecord.create_or_update(
        data=agent_gnd_data, dbcommit=True, reindex=True
    )
    assert action == Action.REPLACE
    assert returned_record["pid"] == "12391664X"

    returned_record, action = AgentReroRecord.create_or_update(
        data=agent_rero_data, dbcommit=True, reindex=True
    )
    assert action == Action.REPLACE
    assert returned_record["pid"] == "A023655346"

    returned_record, action = AgentIdrefRecord.create_or_update(
        data=agent_idref_data, dbcommit=True, reindex=True
    )
    assert action == Action.REPLACE
    assert returned_record["pid"] == "069774331"

    # Test update MD5 agent record with VIAF links.
    returned_record, action = AgentGndRecord.create_or_update(
        data=agent_gnd_data, dbcommit=True, reindex=True, test_md5=True
    )
    assert action == Action.UPTODATE
    assert returned_record["pid"] == "12391664X"

    returned_record, action = AgentReroRecord.create_or_update(
        data=agent_rero_data, dbcommit=True, reindex=True, test_md5=True
    )
    assert action == Action.UPTODATE
    assert returned_record["pid"] == "A023655346"

    returned_record, action = AgentIdrefRecord.create_or_update(
        data=agent_idref_data, dbcommit=True, reindex=True, test_md5=True
    )
    assert action == Action.UPTODATE
    assert returned_record["pid"] == "069774331"

    # VIAF update with delete
    rero_pid = viaf_record.pop("rero_pid")
    viaf_record = viaf_record.update(data=viaf_record, dbcommit=True, reindex=True)
    viaf_record.create_mef_and_agents(dbcommit=True, reindex=True)
    assert viaf_record.get_entities_pids() == [
        {"pid": idref_record.pid, "source": "idref", "record_class": AgentIdrefRecord},
        {"pid": gnd_record.pid, "source": "gnd", "record_class": AgentGndRecord},
    ]
    mef_record_rero = AgentMefRecord.get_mef(
        entity_pid=rero_record.pid, entity_name=rero_record.name
    )[0]
    assert mef_record_rero.get_entities_pids() == [
        {"pid": rero_record.pid, "record_class": AgentReroRecord}
    ]

    # VIAF update with merge
    viaf_record = AgentViafRecord.get_record_by_pid(viaf_record.pid)
    viaf_record["rero_pid"] = rero_pid
    viaf_record = viaf_record.update(data=viaf_record, dbcommit=True, reindex=True)
    viaf_record.create_mef_and_agents(dbcommit=True, reindex=True)
    assert viaf_record.get_entities_pids() == [
        {"pid": idref_record.pid, "source": "idref", "record_class": AgentIdrefRecord},
        {"pid": gnd_record.pid, "source": "gnd", "record_class": AgentGndRecord},
        {"pid": rero_record.pid, "source": "rero", "record_class": AgentReroRecord},
    ]
    mef_record_rero = AgentMefRecord.get_record_by_pid(mef_record_rero.pid)
    assert "rero" not in mef_record_rero

    # VIAF delete
    _, action, mef_actions = viaf_record.delete(dbcommit=True, delindex=True)
    assert action == Action.DELETE
    assert mef_actions == {
        "1": {
            "gnd": {"12391664X": Action.DELETE},
            "idref": {"069774331": Action.UPDATE},
            "rero": {"A023655346": Action.DELETE},
            "viaf": {"66739143": Action.DELETE},
        },
        "3": {"gnd": {"12391664X": Action.CREATE}},
        "4": {"rero": {"A023655346": Action.CREATE}},
    }


def test_get_unlinked_agents_relink_uses_record_id(app):
    """Test relinking uses search hit record id instead of pid lookup."""
    from rero_mef.agents.api import get_unlinked_agents

    fake_viaf_search = _FakeSearch(
        [_FakeHit({"pid": "viaf-1", "gnd_pid": "gnd-1"}, "viaf-record")]
    )
    fake_mef_search = _FakeSearch(
        [_FakeHit({"pid": "mef-1", "gnd": {"pid": "gnd-1"}}, "mef-record-id")]
    )
    fake_record = _FakeRecord({"pid": "mef-1"})

    fake_entity_class = type(
        "FakeEntityClass",
        (),
        {"name": "gnd", "viaf_source_code": "DNB"},
    )

    with (
        mock.patch.dict(app.config, {"RERO_AGENTS": ["agents/gnd"]}),
        mock.patch(
            "rero_mef.agents.viaf.api.AgentViafSearch",
            return_value=fake_viaf_search,
        ),
        mock.patch(
            "rero_mef.agents.mef.api.AgentMefSearch",
            return_value=fake_mef_search,
        ),
        mock.patch(
            "rero_mef.agents.api.get_entity_class", return_value=fake_entity_class
        ),
        mock.patch(
            "rero_mef.agents.mef.api.AgentMefRecord.get_record",
            return_value=fake_record,
        ) as mock_get_record,
        mock.patch(
            "rero_mef.agents.mef.api.AgentMefRecord.get_record_by_pid",
            side_effect=AssertionError("pid lookup should not be used"),
        ),
    ):
        assert not list(get_unlinked_agents(relink=True, dbcommit=True, reindex=True))

    mock_get_record.assert_called_once_with("mef-record-id")
    assert fake_record["viaf_pid"] == "viaf-1"
    assert fake_record.update_calls == [
        {
            "data": {"pid": "mef-1", "viaf_pid": "viaf-1"},
            "dbcommit": True,
            "reindex": True,
        }
    ]


def test_get_unlinked_agents_yields_all_tasks(app):
    """Test get_unlinked_agents yields all tasks lazily from the MEF scan."""
    from rero_mef.agents.api import get_unlinked_agents

    fake_viaf_search = _FakeSearch([])
    fake_mef_search = _FakeSearch(
        [
            _FakeHit({"pid": "mef-1", "gnd": {"pid": "gnd-1"}}, "mef-record-1"),
            _FakeHit({"pid": "mef-2", "gnd": {"pid": "gnd-2"}}, "mef-record-2"),
        ]
    )

    fake_entity_class = type(
        "FakeEntityClass",
        (),
        {"name": "gnd", "viaf_source_code": "DNB"},
    )

    with (
        mock.patch.dict(app.config, {"RERO_AGENTS": ["agents/gnd"]}),
        mock.patch(
            "rero_mef.agents.viaf.api.AgentViafSearch",
            return_value=fake_viaf_search,
        ),
        mock.patch(
            "rero_mef.agents.mef.api.AgentMefSearch",
            return_value=fake_mef_search,
        ),
        mock.patch(
            "rero_mef.agents.api.get_entity_class", return_value=fake_entity_class
        ),
    ):
        tasks = list(get_unlinked_agents(relink=False, dbcommit=False, reindex=False))

    assert tasks == [("mef-1", "DNB", "gnd-1"), ("mef-2", "DNB", "gnd-2")]
    assert fake_mef_search.scan_count == 2


def test_create_or_update_mef_skips_missing_displaced_agent(app):
    """Displaced agent that no longer exists is skipped without raising.

    Regression: get_record_by_pid returns None when a displaced agent has been
    deleted between the consolidation step and the re-MEF step.  The guard must
    log a warning and continue instead of raising AttributeError.
    """
    from rero_mef.agents import AgentGndRecord

    fake_mef = mock.MagicMock()
    fake_mef.pid = "mef-1"
    # Simulate one duplicate MEF record being consolidated: the record holds a
    # reference to "gnd-old" which will be added to old_pids.
    fake_mef.__iter__ = mock.MagicMock(return_value=iter([]))
    fake_mef.pop.return_value = {"$ref": "https://mef.rero.ch/api/agents/gnd/gnd-old"}
    fake_mef.get.return_value = None
    fake_mef.update.return_value = fake_mef

    with (
        mock.patch(
            "rero_mef.agents.mef.api.AgentMefRecord.get_mef",
            return_value=[fake_mef],
        ),
        mock.patch(
            "rero_mef.agents.mef.api.AgentMefRecord.flush_indexes",
        ),
        # The displaced agent is gone from the DB
        mock.patch.object(AgentGndRecord, "get_record_by_pid", return_value=None),
    ):
        record = AgentGndRecord(
            {
                "pid": "gnd-new",
                "type": "bf:Person",
                "authorized_access_point": "New, Author",
            }
        )
        # Must not raise AttributeError
        mef_record, mef_actions = record.create_or_update_mef(
            dbcommit=False, reindex=False
        )

    # The displaced pid was skipped, so it does not appear in mef_actions
    assert "gnd-old" not in mef_actions


def test_agents_utils_get_agent_endpoints(app):
    """get_agent_endpoints returns only agent endpoints from config."""
    from rero_mef.agents.utils import get_agent_endpoints

    endpoints = get_agent_endpoints()
    assert isinstance(endpoints, dict)
    assert "aidref" in endpoints
    assert "aggnd" in endpoints
    assert "agrero" in endpoints


def test_agents_utils_get_agent_classes(app):
    """get_agent_classes returns a list of record classes for each agent endpoint."""
    from rero_mef.agents.utils import get_agent_classes

    classes = get_agent_classes()
    assert isinstance(classes, list)
    assert len(classes) > 0
    assert all(cls is not None for cls in classes)
