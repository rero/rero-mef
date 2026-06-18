# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test concepts api."""

import os
from copy import deepcopy

from rero_mef.api import Action
from rero_mef.concepts import (
    ConceptGndRecord,
    ConceptIdrefRecord,
    ConceptMefRecord,
    ConceptReroRecord,
)
from rero_mef.utils import export_json_records, number_records_in_file

SCHEMA_URL = "https://mef.rero.ch/schemas/concepts_mef"


def _no_md5(record):
    return {k: v for k, v in record.items() if k != "md5"}


def test_create_concept_record(app, concept_rero_data, concept_idref_data, tmpdir):
    """Test create concept record."""
    idref_record, action = ConceptIdrefRecord.create_or_update(
        data=concept_idref_data, dbcommit=True, reindex=True
    )
    assert action == Action.CREATE
    assert idref_record["pid"] == "050548115"

    m_record, m_actions = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {m_record.pid: Action.CREATE}
    assert "md5" in m_record
    assert _no_md5(m_record) == {
        "$schema": f"{SCHEMA_URL}/mef-concept-v0.0.1.json",
        "idref": {"$ref": "https://mef.rero.ch/api/concepts/idref/050548115"},
        "deleted": "2022-09-03T07:07:32.526780+00:00",
        "pid": "1",
        "type": "bf:Topic",
    }

    rero_record, action = ConceptReroRecord.create_or_update(
        data=concept_rero_data, dbcommit=True, reindex=True
    )
    assert action == Action.CREATE
    assert rero_record["pid"] == concept_rero_data["pid"]
    m_record, m_actions = rero_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {m_record.pid: Action.CREATE}
    assert "md5" in m_record
    assert _no_md5(m_record) == {
        "$schema": f"{SCHEMA_URL}/mef-concept-v0.0.1.json",
        "rero": {
            "$ref": f"https://mef.rero.ch/api/concepts/rero/{concept_rero_data['pid']}"
        },
        "pid": "2",
        "type": "bf:Topic",
    }

    mef_rec_resolved = m_record.replace_refs()
    assert mef_rec_resolved.get("rero").get("pid") == rero_record.pid

    # Test JSON export.
    tmp_file_name = os.path.join(tmpdir, "mef.json")
    export_json_records(
        pids=ConceptMefRecord.get_all_pids(),
        pid_type="comef",
        output_file_name=tmp_file_name,
    )
    assert number_records_in_file(tmp_file_name, "json") == 2
    assert "$schema" in open(tmp_file_name).read()
    export_json_records(
        pids=ConceptMefRecord.get_all_pids(),
        pid_type="comef",
        output_file_name=tmp_file_name,
        schema=False,
    )
    assert number_records_in_file(tmp_file_name, "json") == 2
    assert "$schema" not in open(tmp_file_name).read()

    # Test update concept record.
    returned_record, action = ConceptReroRecord.create_or_update(
        data=concept_rero_data, dbcommit=True, reindex=True
    )
    assert action == Action.REPLACE
    assert returned_record["pid"] == concept_rero_data["pid"]

    returned_record, action = ConceptIdrefRecord.create_or_update(
        data=concept_idref_data, dbcommit=True, reindex=True
    )
    assert action == Action.REPLACE
    assert returned_record["pid"] == concept_idref_data["pid"]

    # Test update MD5 concept record MD5 tewst.
    returned_record, action = ConceptReroRecord.create_or_update(
        data=concept_rero_data, dbcommit=True, reindex=True, test_md5=True
    )
    assert action == Action.UPTODATE
    assert returned_record["pid"] == concept_rero_data["pid"]

    returned_record, action = ConceptIdrefRecord.create_or_update(
        data=concept_idref_data, dbcommit=True, reindex=True, test_md5=True
    )
    assert action == Action.UPTODATE
    assert returned_record["pid"] == concept_idref_data["pid"]

    idref_record = ConceptIdrefRecord.get_record_by_pid(idref_record.pid)
    idref_record["type"] = "bf:Temporal"
    idref_record.update(data=idref_record, dbcommit=True, reindex=True)

    ConceptMefRecord.flush_indexes()

    m_record, m_actions = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {m_record.pid: Action.REPLACE}
    assert "md5" in m_record
    assert _no_md5(m_record) == {
        "$schema": f"{SCHEMA_URL}/mef-concept-v0.0.1.json",
        "idref": {
            "$ref": f"https://mef.rero.ch/api/concepts/idref/{concept_idref_data['pid']}"
        },
        "deleted": "2022-09-03T07:07:32.526780+00:00",
        "pid": "1",
        "type": "bf:Temporal",
    }


def test_create_concept_frbnf_record(
    app, concept_idref_frbnf_data_close, concept_gnd_frbnf_data_close, tmpdir
):
    """Test create concept record with frbnf links."""
    mef_count = ConceptMefRecord.count()
    # Create idref record with identifiedBy `FRBNF12352687`.
    idref_record, action = ConceptIdrefRecord.create_or_update(
        data=concept_idref_frbnf_data_close, dbcommit=True, reindex=True
    )
    assert action == Action.CREATE
    assert idref_record["pid"] == concept_idref_frbnf_data_close["pid"]

    # Create or update MEF record.
    m_record, m_actions = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {m_record.pid: Action.CREATE}
    assert "md5" in m_record
    assert _no_md5(m_record) == {
        "$schema": f"{SCHEMA_URL}/mef-concept-v0.0.1.json",
        "idref": {
            "$ref": f"https://mef.rero.ch/api/concepts/idref/{concept_idref_frbnf_data_close['pid']}"
        },
        "pid": f"{mef_count + 1}",
        "type": "bf:Topic",
    }

    # Create gnd record with closeMatch identifiedBy `FRBNF12352687`
    gnd_record, action = ConceptGndRecord.create_or_update(
        data=concept_gnd_frbnf_data_close, dbcommit=True, reindex=True
    )
    assert action == Action.CREATE
    assert gnd_record["pid"] == concept_gnd_frbnf_data_close["pid"]

    ConceptIdrefRecord.flush_indexes()
    # Create or update MEF record (should be the same as for IDREF)

    m_record, m_actions = gnd_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {m_record.pid: Action.REPLACE}
    assert "md5" in m_record
    assert _no_md5(m_record) == {
        "$schema": f"{SCHEMA_URL}/mef-concept-v0.0.1.json",
        "gnd": {
            "$ref": f"https://mef.rero.ch/api/concepts/gnd/{concept_gnd_frbnf_data_close['pid']}"
        },
        "idref": {
            "$ref": f"https://mef.rero.ch/api/concepts/idref/{concept_idref_frbnf_data_close['pid']}"
        },
        "pid": f"{mef_count + 1}",
        "type": "bf:Topic",
    }

    assert idref_record.association_identifier == "FRBNF12352687"
    assert gnd_record.association_identifier == "FRBNF12352687"

    # Delete identifiedBy `FRBNF12352687` from IDREF record
    idref_record["identifiedBy"] = [
        {"source": "IDREF", "type": "uri", "value": "http://www.idref.fr/032510934"},
    ]
    idref_record, action = ConceptIdrefRecord.create_or_update(
        data=idref_record, dbcommit=True, reindex=True
    )
    assert action == Action.REPLACE
    assert idref_record["identifiedBy"] == [
        {"source": "IDREF", "type": "uri", "value": "http://www.idref.fr/032510934"},
    ]

    # Create or update MEF record for IDREF.
    # We should update the old MEF IDREF record and recreate a new MEF GND record.
    m_record, m_actions = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {
        m_record.pid: Action.REPLACE,
        f"{mef_count + 2}": Action.CREATE,
    }
    assert "md5" in m_record
    assert _no_md5(m_record) == {
        "$schema": f"{SCHEMA_URL}/mef-concept-v0.0.1.json",
        "idref": {
            "$ref": f"https://mef.rero.ch/api/concepts/idref/{concept_idref_frbnf_data_close['pid']}"
        },
        "pid": f"{mef_count + 1}",
        "type": "bf:Topic",
    }

    # Add identifiedBy `FRBNF12352687` to IDREF record
    idref_record["identifiedBy"] = [
        {
            "source": "IDREF",
            "type": "uri",
            "value": f"http://www.idref.fr/{concept_idref_frbnf_data_close['pid']}",
        },
        {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF12352687"},
    ]
    idref_record, action = ConceptIdrefRecord.create_or_update(
        data=idref_record, dbcommit=True, reindex=True
    )
    assert action == Action.REPLACE
    assert idref_record["identifiedBy"] == [
        {
            "source": "IDREF",
            "type": "uri",
            "value": f"http://www.idref.fr/{concept_idref_frbnf_data_close['pid']}",
        },
        {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF12352687"},
    ]

    # Create or update MEF record for IDREF
    # We should update MEF IDREF record and delete ref from MEF GND record.
    m_record, m_actions = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {
        m_record.pid: Action.REPLACE,
        f"{mef_count + 2}": Action.DELETE_ENTITY,
    }
    assert "md5" in m_record
    assert _no_md5(m_record) == {
        "$schema": f"{SCHEMA_URL}/mef-concept-v0.0.1.json",
        "idref": {
            "$ref": f"https://mef.rero.ch/api/concepts/idref/{concept_idref_frbnf_data_close['pid']}"
        },
        "gnd": {
            "$ref": f"https://mef.rero.ch/api/concepts/gnd/{concept_gnd_frbnf_data_close['pid']}"
        },
        "pid": f"{mef_count + 1}",
        "type": "bf:Topic",
    }

    # Delete identifiedBy `FRBNF12352687` from GND record.
    close_match = gnd_record.pop("closeMatch")
    gnd_record, action = ConceptGndRecord.create_or_update(
        data=gnd_record, dbcommit=True, reindex=True
    )
    assert action == Action.REPLACE
    assert not idref_record.get("closeMatch")

    # Create or update MEF record for IDREF
    # We should update MEF IDREF record and delete ref from MEF GND record.
    m_record, m_actions = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {
        m_record.pid: Action.REPLACE,
        f"{mef_count + 3}": Action.CREATE,
    }
    assert "md5" in m_record
    assert _no_md5(m_record) == {
        "$schema": f"{SCHEMA_URL}/mef-concept-v0.0.1.json",
        "idref": {
            "$ref": f"https://mef.rero.ch/api/concepts/idref/{concept_idref_frbnf_data_close['pid']}"
        },
        "pid": f"{mef_count + 1}",
        "type": "bf:Topic",
    }

    # Add identifiedBy `FRBNF12352687` to GND record
    gnd_record["exactMatch"] = close_match
    gnd_record, action = ConceptGndRecord.create_or_update(
        data=gnd_record, dbcommit=True, reindex=True
    )
    assert action == Action.REPLACE
    assert gnd_record.get("exactMatch") == close_match

    # Create or update MEF record for GND
    # We should update MEF GND record delete ref and MEF IDREF update.
    m_record, m_actions = gnd_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {
        m_record.pid: Action.REPLACE,
        f"{mef_count + 1}": Action.DELETE_ENTITY,
    }
    assert "md5" in m_record
    assert _no_md5(m_record) == {
        "$schema": f"{SCHEMA_URL}/mef-concept-v0.0.1.json",
        "gnd": {
            "$ref": f"https://mef.rero.ch/api/concepts/gnd/{concept_gnd_frbnf_data_close['pid']}"
        },
        "idref": {
            "$ref": f"https://mef.rero.ch/api/concepts/idref/{concept_idref_frbnf_data_close['pid']}"
        },
        "pid": m_record.pid,
        "type": "bf:Topic",
    }

    # Add second GND with `FRBNF12352687` in close match
    gnd_record_close_match = deepcopy(gnd_record)
    gnd_record_close_match["pid"] = f"{gnd_record_close_match['pid']}_2"
    match = gnd_record_close_match.pop("exactMatch")
    gnd_record_close_match["closeMatch"] = match
    gnd_record_close_match = ConceptGndRecord.create(
        data=gnd_record_close_match, dbcommit=True, reindex=True
    )
    ConceptGndRecord.flush_indexes()
    m_record, m_actions = idref_record.create_or_update_mef(dbcommit=True, reindex=True)

    assert m_actions == {m_record.pid: Action.REPLACE}
    assert "md5" in m_record
    assert _no_md5(m_record) == {
        "$schema": f"{SCHEMA_URL}/mef-concept-v0.0.1.json",
        "gnd": {
            "$ref": f"https://mef.rero.ch/api/concepts/gnd/{concept_gnd_frbnf_data_close['pid']}"
        },
        "idref": {
            "$ref": f"https://mef.rero.ch/api/concepts/idref/{concept_idref_frbnf_data_close['pid']}"
        },
        "pid": f"{m_record.pid}",
        "type": "bf:Topic",
    }

    # Change exact match to close match
    match = gnd_record.pop("exactMatch")
    gnd_record["closeMatch"] = match
    gnd_record = ConceptGndRecord.create_or_update(
        data=gnd_record, dbcommit=True, reindex=True
    )
    ConceptGndRecord.flush_indexes()
    m_record, m_actions = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    mef_count = ConceptMefRecord.count()
    assert m_actions == {m_record.pid: Action.REPLACE, str(mef_count): Action.CREATE}
    assert "md5" in m_record
    assert _no_md5(m_record) == {
        "$schema": f"{SCHEMA_URL}/mef-concept-v0.0.1.json",
        "idref": {
            "$ref": f"https://mef.rero.ch/api/concepts/idref/{concept_idref_frbnf_data_close['pid']}"
        },
        "pid": f"{m_record.pid}",
        "type": "bf:Topic",
    }


def test_create_concept_frbnf_record_exact(
    app, concept_idref_frbnf_data_exact, concept_gnd_frbnf_data_exact, tmpdir
):
    """Test create concept record with frbnf links."""
    mef_count = ConceptMefRecord.count()
    # Create idref record with identifiedBy `FRBNF12352687`.
    idref_record, action = ConceptIdrefRecord.create_or_update(
        data=concept_idref_frbnf_data_exact, dbcommit=True, reindex=True
    )
    assert action == Action.CREATE
    assert idref_record["pid"] == concept_idref_frbnf_data_exact["pid"]

    gnd_record, action = ConceptGndRecord.create_or_update(
        data=concept_gnd_frbnf_data_exact, dbcommit=True, reindex=True
    )
    assert action == Action.CREATE
    assert gnd_record["pid"] == concept_gnd_frbnf_data_exact["pid"]

    ConceptIdrefRecord.flush_indexes()
    ConceptGndRecord.flush_indexes()
    # Create or update MEF record.
    m_record, m_actions = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {m_record.pid: Action.CREATE}
    assert "md5" in m_record
    assert _no_md5(m_record) == {
        "$schema": f"{SCHEMA_URL}/mef-concept-v0.0.1.json",
        "idref": {
            "$ref": f"https://mef.rero.ch/api/concepts/idref/{concept_idref_frbnf_data_exact['pid']}"
        },
        "gnd": {
            "$ref": f"https://mef.rero.ch/api/concepts/gnd/{concept_gnd_frbnf_data_exact['pid']}"
        },
        "pid": f"{mef_count + 1}",
        "type": "bf:Topic",
    }


def test_concept_record_delete(app, concept_idref_data):
    """ConceptRecord.delete removes the ref from linked MEF records."""
    idref_record, _ = ConceptIdrefRecord.create_or_update(
        data=deepcopy(concept_idref_data), dbcommit=True, reindex=True
    )
    m_record, _ = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_record.get("idref") is not None

    idref_record.delete(dbcommit=True, delindex=True)
    updated_mef = ConceptMefRecord.get_record_by_pid(m_record.pid)
    assert updated_mef is None or updated_mef.get("idref") is None


def test_concepts_utils_get_concept_endpoints(app):
    """get_concept_endpoints returns only concept endpoints from config."""
    from rero_mef.concepts.utils import get_concept_endpoints

    endpoints = get_concept_endpoints()
    assert isinstance(endpoints, dict)
    assert "cidref" in endpoints
    assert "cognd" in endpoints
    assert "corero" in endpoints


def test_concepts_utils_get_concept_classes(app):
    """get_concept_classes returns record classes keyed by endpoint, without comef by default."""
    from rero_mef.concepts.utils import get_concept_classes

    classes = get_concept_classes()
    assert isinstance(classes, dict)
    assert "comef" not in classes
    assert len(classes) > 0

    classes_with_mef = get_concept_classes(without_mef=False)
    assert isinstance(classes_with_mef, dict)
    assert len(classes_with_mef) >= len(classes)
