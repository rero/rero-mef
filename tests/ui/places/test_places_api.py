# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2024 RERO
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

"""Test places api."""

import os

from rero_mef.api import Action
from rero_mef.places import (
    PlaceGndRecord,
    PlaceIdrefRecord,
    PlaceMefRecord,
    PlaceMefSearch,
)
from rero_mef.utils import export_json_records, number_records_in_file

SCHEMA_URL = "https://mef.rero.ch/schemas/places_mef"


def test_create_place_record(app, place_idref_data, place_gnd_data, tmpdir):
    """Test create place record links."""
    idref_record, action = PlaceIdrefRecord.create_or_update(
        data=place_idref_data, dbcommit=True, reindex=True
    )
    assert action == Action.CREATE
    assert idref_record["pid"] == "271330163"

    m_idref_record, m_action = idref_record.create_or_update_mef(
        dbcommit=True, reindex=True
    )
    assert m_action == {"1": Action.CREATE}
    assert m_idref_record == {
        "$schema": f"{SCHEMA_URL}/mef-place-v0.0.1.json",
        "idref": {"$ref": "https://mef.rero.ch/api/places/idref/271330163"},
        "deleted": "2022-09-03T07:07:32.526780+00:00",
        "pid": "1",
        "type": "bf:Place",
    }

    # Test JSON export.
    tmp_file_name = os.path.join(tmpdir, "mef.json")
    export_json_records(
        pids=PlaceMefRecord.get_all_pids(),
        pid_type="plmef",
        output_file_name=tmp_file_name,
    )
    assert number_records_in_file(tmp_file_name, "json") == 1
    assert "$schema" in open(tmp_file_name).read()
    export_json_records(
        pids=PlaceMefRecord.get_all_pids(),
        pid_type="plmef",
        output_file_name=tmp_file_name,
        schema=False,
    )
    assert number_records_in_file(tmp_file_name, "json") == 1
    assert "$schema" not in open(tmp_file_name).read()

    returned_record, action = PlaceIdrefRecord.create_or_update(
        data=place_idref_data, dbcommit=True, reindex=True
    )
    assert action == Action.UPDATE
    assert returned_record["pid"] == "271330163"

    # Test update MD5 place record MD5 test.
    returned_record, action = PlaceIdrefRecord.create_or_update(
        data=place_idref_data, dbcommit=True, reindex=True, test_md5=True
    )
    assert action == Action.UPTODATE
    assert returned_record["pid"] == "271330163"

    PlaceMefRecord.flush_indexes()
    # GND tests
    gnd_record, action = PlaceGndRecord.create_or_update(
        data=place_gnd_data, dbcommit=True, reindex=True
    )
    assert action == Action.CREATE
    assert gnd_record["pid"] == "040754766"

    PlaceMefRecord.flush_indexes()
    m_gnd_record, m_action = gnd_record.create_or_update_mef(
        dbcommit=True, reindex=True
    )
    assert m_action == {"2": Action.CREATE}
    assert m_gnd_record == {
        "$schema": f"{SCHEMA_URL}/mef-place-v0.0.1.json",
        "gnd": {"$ref": "https://mef.rero.ch/api/places/gnd/040754766"},
        "pid": "2",
        "type": "bf:Place",
    }

    idref_record = PlaceIdrefRecord.get_record_by_pid(idref_record.pid)
    idref_record.setdefault("identifiedBy", []).append(
        {"source": "GND", "value": "(DE-101)040754766", "type": "bf:Nbn"}
    )
    idref_record = idref_record.update(data=idref_record, dbcommit=True, reindex=True)

    PlaceMefRecord.flush_indexes()
    m_idref_record, m_action = idref_record.create_or_update_mef(
        dbcommit=True, reindex=True
    )
    assert m_action == {"1": Action.UPDATE, "2": Action.DELETE_AGENT}
    assert m_idref_record == {
        "$schema": f"{SCHEMA_URL}/mef-place-v0.0.1.json",
        "deleted": "2022-09-03T07:07:32.526780+00:00",
        "idref": {"$ref": "https://mef.rero.ch/api/places/idref/271330163"},
        "gnd": {"$ref": "https://mef.rero.ch/api/places/gnd/040754766"},
        "pid": "1",
        "type": "bf:Place",
    }
    assert PlaceMefSearch().filter("term", gnd__pid="040754766").count() == 1

    for identified_by in idref_record["identifiedBy"]:
        if identified_by.get("source") == "GND":
            identified_by["value"] = "(DE-101)TEST"
    idref_record = idref_record.update(data=idref_record, dbcommit=True, reindex=True)

    PlaceMefRecord.flush_indexes()
    m_idref_record, m_action = idref_record.create_or_update_mef(
        dbcommit=True, reindex=True
    )
    assert m_action == {"1": Action.UPDATE, "3": Action.CREATE}
    assert m_idref_record == {
        "$schema": f"{SCHEMA_URL}/mef-place-v0.0.1.json",
        "deleted": "2022-09-03T07:07:32.526780+00:00",
        "idref": {"$ref": "https://mef.rero.ch/api/places/idref/271330163"},
        "pid": "1",
        "type": "bf:Place",
    }

    m_record = PlaceMefRecord.get_record_by_pid("3")
    assert m_record == {
        "$schema": f"{SCHEMA_URL}/mef-place-v0.0.1.json",
        "gnd": {"$ref": "https://mef.rero.ch/api/places/gnd/040754766"},
        "pid": "3",
        "type": "bf:Place",
    }

    place_gnd_data["pid"] = "TEST"
    gnd_record, action = PlaceGndRecord.create_or_update(
        data=place_gnd_data, dbcommit=True, reindex=True
    )
    assert action == Action.CREATE
    assert gnd_record["pid"] == "TEST"

    PlaceIdrefRecord.flush_indexes()
    PlaceMefRecord.flush_indexes()
    m_gnd_record, m_action = gnd_record.create_or_update_mef(
        dbcommit=True, reindex=True
    )
    assert m_action == {"1": Action.UPDATE}
    assert m_gnd_record == {
        "$schema": f"{SCHEMA_URL}/mef-place-v0.0.1.json",
        "deleted": "2022-09-03T07:07:32.526780+00:00",
        "idref": {"$ref": "https://mef.rero.ch/api/places/idref/271330163"},
        "gnd": {"$ref": "https://mef.rero.ch/api/places/gnd/TEST"},
        "pid": "1",
        "type": "bf:Place",
    }
