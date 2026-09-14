# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test api."""

from rero_mef.agents import (
    AgentIdrefIndexer,
    AgentIdrefRecord,
    AgentMefRecord,
    AgentMefSearch,
)
from rero_mef.api import Action
from rero_mef.tasks import process_bulk_queue


def test_entityrecord_api(app, agent_idref_record):
    """Test EntityRecord api."""
    idref = agent_idref_record
    assert AgentIdrefRecord.count() == 1
    assert AgentIdrefRecord.index_all() == 1

    assert AgentIdrefRecord.get_metadata_identifier_names() == (
        "agent_idref_metadata",
        "agent_idref_id",
    )

    count = sum(1 for _ in AgentIdrefRecord.get_all_records())
    assert count == 1

    _, agent_action = AgentIdrefRecord.create_or_update(data=dict(idref), dbcommit=True, reindex=True, test_md5=True)
    assert agent_action == Action.UPTODATE

    mef_record, _ = idref.create_or_update_mef(dbcommit=True, reindex=True)

    idref["gender"] = "female"
    _, agent_action = AgentIdrefRecord.create_or_update(data=dict(idref), dbcommit=True, reindex=True, test_md5=True)
    assert agent_action == Action.REPLACE
    AgentMefRecord.flush_indexes()
    mef_es = next(AgentMefSearch().filter("term", pid=mef_record.pid).scan()).to_dict()
    assert mef_es.get("idref").get("gender") == "female"

    assert AgentIdrefRecord.get_pid_by_id(idref.id) == idref.pid

    AgentIdrefIndexer().bulk_index(list(AgentIdrefRecord.get_all_ids()))
    indexed, failed = process_bulk_queue(stats_only=True)
    assert indexed >= 1
    assert failed == 0


def test_create_or_update_keeps_the_first_deletion_stamp(app, agent_idref_record):
    """A re-delivered tombstone keeps the stamp of the harvest that first saw it.

    No source states when it deleted a record, so the transformations stamp `deleted` with the time they run. Were
    that stamp taken every time, a tombstone would get a new md5 on every harvest that re-delivers it and `test_md5`
    could never skip one.
    """
    first_seen = "2024-10-30T16:33:23.000000+00:00"
    harvested = {k: v for k, v in agent_idref_record.items() if k not in ("md5", "$schema")}

    record, action = AgentIdrefRecord.create_or_update(
        data=harvested | {"deleted": first_seen}, dbcommit=True, reindex=True, test_md5=True
    )
    assert action == Action.REPLACE
    assert record["deleted"] == first_seen

    # the next harvest transforms the same unchanged MARC record and stamps `deleted` again
    record, action = AgentIdrefRecord.create_or_update(
        data=harvested | {"deleted": "2026-09-10T06:14:41.024409+00:00"},
        dbcommit=True,
        reindex=True,
        test_md5=True,
    )
    assert action == Action.UPTODATE
    assert record["deleted"] == first_seen


def test_create_or_update_discards_an_unknown_deleted_record(app, agent_idref_data):
    """A record already deleted at the source before we held it is not created.

    Creating a tombstone for it, and a MEF record alongside, could never be cleaned up: the next harvest reaching
    the same date range would create both again.
    """
    unknown = dict(agent_idref_data) | {"pid": "031243762", "deleted": "2026-09-10T06:14:41.024409+00:00"}
    before = AgentIdrefRecord.count()

    record, action = AgentIdrefRecord.create_or_update(data=unknown, dbcommit=True, reindex=True, test_md5=True)

    assert action == Action.DISCARD
    assert record is None
    assert AgentIdrefRecord.count() == before
    assert AgentIdrefRecord.get_record_by_pid("031243762") is None


def test_create_or_update_deletes_a_record_that_lost_its_access_point(app, agent_idref_data):
    """A record the source stops naming is deleted, and taken out of its MEF record.

    Keeping it would serve a heading the source has dropped: the `copy_fields` merge puts the old one back, the md5
    then matches and the harvest even reports `uptodate`.
    """
    named = dict(agent_idref_data) | {"pid": "099999991"}
    record, action = AgentIdrefRecord.create_or_update(data=named, dbcommit=True, reindex=True)
    assert action == Action.CREATE
    mef_record, _ = record.create_or_update_mef(dbcommit=True, reindex=True)
    assert mef_record.get("idref")

    unnamed = {k: v for k, v in named.items() if k != "authorized_access_point"}
    record, action = AgentIdrefRecord.create_or_update(data=unnamed, dbcommit=True, reindex=True)

    assert action == Action.DELETE
    assert record is None
    assert AgentIdrefRecord.get_record_by_pid("099999991") is None
    # the MEF record held nothing else, so it went too rather than being stranded empty
    assert AgentMefRecord.get_record_by_pid(mef_record.pid) is None


def test_create_or_update_keeps_a_record_the_source_redirected(app, agent_idref_data):
    """A redirect states no heading, but it is where the pid went and has to stay.

    `EntityMefRecord.get_latest` reads `relation_pid` to send a request for the old pid on to the new record;
    deleting the redirect would answer that request with nothing.
    """
    named = dict(agent_idref_data) | {"pid": "099999992"}
    record, action = AgentIdrefRecord.create_or_update(data=named, dbcommit=True, reindex=True)
    assert action == Action.CREATE
    heading = record["authorized_access_point"]

    # what the source sends for a redirected record: the pointer, and no name at all
    redirected = {
        "$schema": named["$schema"],
        "pid": "099999992",
        "deleted": "2026-09-10T06:14:41.024409+00:00",
        "relation_pid": {"type": "redirect_to", "value": "099999993"},
    }
    record, action = AgentIdrefRecord.create_or_update(data=redirected, dbcommit=True, reindex=True)

    assert action == Action.REPLACE
    assert record["relation_pid"] == {"type": "redirect_to", "value": "099999993"}
    assert AgentIdrefRecord.get_record_by_pid("099999992") is not None
    # the heading the harvest no longer states is kept, so the record still names what it redirects from
    assert record["authorized_access_point"] == heading
    assert AgentIdrefRecord.get_record_by_pid("099999992")["authorized_access_point"] == heading
