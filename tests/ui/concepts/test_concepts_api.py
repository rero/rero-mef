# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2020 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Test concepts api."""

import os

from rero_mef.api import Action
from rero_mef.concepts import (
    ConceptGndRecord,
    ConceptIdrefRecord,
    ConceptMefRecord,
    ConceptReroRecord,
)
from rero_mef.utils import export_json_records, number_records_in_file

SCHEMA_URL = "https://mef.rero.ch/schemas/concepts_mef"


def test_create_concept_record(app, concept_rero_data, concept_idref_data, tmpdir):
    """Test create concept record."""
    idref_record, action = ConceptIdrefRecord.create_or_update(
        data=concept_idref_data, dbcommit=True, reindex=True
    )
    assert action == Action.CREATE
    assert idref_record["pid"] == "050548115"

    m_record, m_actions = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {m_record.pid: Action.CREATE}
    assert m_record == {
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
    assert m_record == {
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
    assert action == Action.UPDATE
    assert returned_record["pid"] == concept_rero_data["pid"]

    returned_record, action = ConceptIdrefRecord.create_or_update(
        data=concept_idref_data, dbcommit=True, reindex=True
    )
    assert action == Action.UPDATE
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
    assert m_actions == {m_record.pid: Action.UPDATE}
    assert m_record == {
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
    assert m_record == {
        "$schema": f"{SCHEMA_URL}/mef-concept-v0.0.1.json",
        "idref": {
            "$ref": f"https://mef.rero.ch/api/concepts/idref/{concept_idref_frbnf_data_close['pid']}"
        },
        "pid": f"{mef_count+1}",
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
    assert m_actions == {m_record.pid: Action.UPDATE}

    assert m_record == {
        "$schema": f"{SCHEMA_URL}/mef-concept-v0.0.1.json",
        "gnd": {
            "$ref": f"https://mef.rero.ch/api/concepts/gnd/{concept_gnd_frbnf_data_close['pid']}"
        },
        "idref": {
            "$ref": f"https://mef.rero.ch/api/concepts/idref/{concept_idref_frbnf_data_close['pid']}"
        },
        "pid": f"{mef_count+1}",
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
    assert action == Action.UPDATE
    assert idref_record["identifiedBy"] == [
        {"source": "IDREF", "type": "uri", "value": "http://www.idref.fr/032510934"},
    ]

    # Create or update MEF record for IDREF.
    # We should update the old MEF IDREF record and recreate a new MEF GND record.
    m_record, m_actions = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {m_record.pid: Action.UPDATE, f"{mef_count+2}": Action.CREATE}
    assert m_record == {
        "$schema": f"{SCHEMA_URL}/mef-concept-v0.0.1.json",
        "idref": {
            "$ref": f"https://mef.rero.ch/api/concepts/idref/{concept_idref_frbnf_data_close['pid']}"
        },
        "pid": f"{mef_count+1}",
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
    assert action == Action.UPDATE
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
        m_record.pid: Action.UPDATE,
        f"{mef_count+2}": Action.DELETE_ENTITY,
    }
    assert m_record == {
        "$schema": f"{SCHEMA_URL}/mef-concept-v0.0.1.json",
        "idref": {
            "$ref": f"https://mef.rero.ch/api/concepts/idref/{concept_idref_frbnf_data_close['pid']}"
        },
        "gnd": {
            "$ref": f"https://mef.rero.ch/api/concepts/gnd/{concept_gnd_frbnf_data_close['pid']}"
        },
        "pid": f"{mef_count+1}",
        "type": "bf:Topic",
    }

    # Delete identifiedBy `FRBNF12352687` from GND record.
    close_match = gnd_record.pop("closeMatch")
    gnd_record, action = ConceptGndRecord.create_or_update(
        data=gnd_record, dbcommit=True, reindex=True
    )
    assert action == Action.UPDATE
    assert not idref_record.get("closeMatch")

    # Create or update MEF record for IDREF
    # We should update MEF IDREF record and delete ref from MEF GND record.
    m_record, m_actions = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {
        m_record.pid: Action.UPDATE,
        f"{mef_count+3}": Action.CREATE,
    }
    assert m_record == {
        "$schema": f"{SCHEMA_URL}/mef-concept-v0.0.1.json",
        "idref": {
            "$ref": f"https://mef.rero.ch/api/concepts/idref/{concept_idref_frbnf_data_close['pid']}"
        },
        "pid": f"{mef_count+1}",
        "type": "bf:Topic",
    }

    # Add identifiedBy `FRBNF12352687` to GND record
    gnd_record["exactMatch"] = close_match
    gnd_record, action = ConceptGndRecord.create_or_update(
        data=gnd_record, dbcommit=True, reindex=True
    )
    assert action == Action.UPDATE
    assert gnd_record.get("exactMatch") == close_match

    # Create or update MEF record for GND
    # We should update MEF GND record delete ref and MEF IDREF update.
    m_record, m_actions = gnd_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {
        m_record.pid: Action.UPDATE,
        f"{mef_count+1}": Action.DELETE_ENTITY,
    }
    assert m_record == {
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
    assert m_record == {
        "$schema": f"{SCHEMA_URL}/mef-concept-v0.0.1.json",
        "idref": {
            "$ref": f"https://mef.rero.ch/api/concepts/idref/{concept_idref_frbnf_data_exact['pid']}"
        },
        "gnd": {
            "$ref": f"https://mef.rero.ch/api/concepts/gnd/{concept_gnd_frbnf_data_exact['pid']}"
        },
        "pid": f"{mef_count+1}",
        "type": "bf:Topic",
    }
