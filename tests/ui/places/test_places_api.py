# RERO MEF
# Copyright (C) 2026 RERO
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


def _no_md5(record):
    return {k: v for k, v in record.items() if k != "md5"}


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
    assert "md5" in m_idref_record
    assert _no_md5(m_idref_record) == {
        "$schema": f"{SCHEMA_URL}/mef-place-v0.0.1.json",
        "idref": {"$ref": "https://mef.rero.ch/api/places/idref/271330163"},
        "pid": "1",
        "type": "bf:Place",
    }
    PlaceMefRecord.flush_indexes()
    m_idref_record, m_action = idref_record.create_or_update_mef(
        dbcommit=True, reindex=True
    )
    assert m_action == {"1": Action.REPLACE}
    assert "md5" in m_idref_record
    assert _no_md5(m_idref_record) == {
        "$schema": f"{SCHEMA_URL}/mef-place-v0.0.1.json",
        "idref": {"$ref": "https://mef.rero.ch/api/places/idref/271330163"},
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
    assert action == Action.REPLACE
    assert returned_record["pid"] == "271330163"

    # Test update MD5 place record MD5 test.
    returned_record, action = PlaceIdrefRecord.create_or_update(
        data=place_idref_data, dbcommit=True, reindex=True, test_md5=True
    )
    assert action == Action.UPTODATE
    assert returned_record["pid"] == "271330163"

    PlaceMefRecord.flush_indexes()
    # Test GND create
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
    assert "md5" in m_gnd_record
    assert _no_md5(m_gnd_record) == {
        "$schema": f"{SCHEMA_URL}/mef-place-v0.0.1.json",
        "gnd": {"$ref": "https://mef.rero.ch/api/places/gnd/040754766"},
        "pid": "2",
        "type": "bf:Place",
    }

    # Test IDREF create with GND ref
    idref_record = PlaceIdrefRecord.get_record_by_pid(idref_record.pid)
    idref_record.setdefault("identifiedBy", []).append(
        {"source": "GND", "value": "(DE-101)040754766", "type": "bf:Nbn"}
    )
    idref_record = idref_record.update(data=idref_record, dbcommit=True, reindex=True)

    PlaceMefRecord.flush_indexes()
    m_idref_record, m_action = idref_record.create_or_update_mef(
        dbcommit=True, reindex=True
    )
    assert m_action == {"1": Action.REPLACE, "2": Action.DELETE_ENTITY}
    assert "md5" in m_idref_record
    assert _no_md5(m_idref_record) == {
        "$schema": f"{SCHEMA_URL}/mef-place-v0.0.1.json",
        "idref": {"$ref": "https://mef.rero.ch/api/places/idref/271330163"},
        "gnd": {"$ref": "https://mef.rero.ch/api/places/gnd/040754766"},
        "pid": "1",
        "type": "bf:Place",
    }
    PlaceMefRecord.flush_indexes()
    assert PlaceMefSearch().filter("term", gnd__pid="040754766").count() == 1

    # Retest IDREF and GND record MEF update
    m_idref_record, m_action = idref_record.create_or_update_mef(
        dbcommit=True, reindex=True
    )
    assert m_action == {"1": Action.REPLACE}
    assert "md5" in m_idref_record
    assert _no_md5(m_idref_record) == {
        "$schema": f"{SCHEMA_URL}/mef-place-v0.0.1.json",
        "idref": {"$ref": "https://mef.rero.ch/api/places/idref/271330163"},
        "gnd": {"$ref": "https://mef.rero.ch/api/places/gnd/040754766"},
        "pid": "1",
        "type": "bf:Place",
    }
    m_gnd_record, m_action = gnd_record.create_or_update_mef(
        dbcommit=True, reindex=True
    )
    assert m_action == {"1": Action.REPLACE}
    assert "md5" in m_gnd_record
    assert _no_md5(m_gnd_record) == {
        "$schema": f"{SCHEMA_URL}/mef-place-v0.0.1.json",
        "idref": {"$ref": "https://mef.rero.ch/api/places/idref/271330163"},
        "gnd": {"$ref": "https://mef.rero.ch/api/places/gnd/040754766"},
        "pid": "1",
        "type": "bf:Place",
    }

    # Test IDREF GND ref change
    for identified_by in idref_record["identifiedBy"]:
        if identified_by.get("source") == "GND":
            identified_by["value"] = "(DE-101)TEST"
    idref_record = idref_record.update(data=idref_record, dbcommit=True, reindex=True)

    PlaceMefRecord.flush_indexes()
    m_idref_record, m_action = idref_record.create_or_update_mef(
        dbcommit=True, reindex=True
    )
    assert m_action == {"1": Action.REPLACE, "3": Action.CREATE}
    assert "md5" in m_idref_record
    assert _no_md5(m_idref_record) == {
        "$schema": f"{SCHEMA_URL}/mef-place-v0.0.1.json",
        "idref": {"$ref": "https://mef.rero.ch/api/places/idref/271330163"},
        "pid": "1",
        "type": "bf:Place",
    }

    m_record = PlaceMefRecord.get_record_by_pid("3")
    assert "md5" in m_record
    assert _no_md5(m_record) == {
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
    PlaceGndRecord.flush_indexes()
    PlaceMefRecord.flush_indexes()

    m_gnd_record, m_action = gnd_record.create_or_update_mef(
        dbcommit=True, reindex=True
    )
    assert m_action == {"1": Action.REPLACE}
    assert "md5" in m_gnd_record
    assert _no_md5(m_gnd_record) == {
        "$schema": f"{SCHEMA_URL}/mef-place-v0.0.1.json",
        "idref": {"$ref": "https://mef.rero.ch/api/places/idref/271330163"},
        "gnd": {"$ref": "https://mef.rero.ch/api/places/gnd/TEST"},
        "pid": "1",
        "type": "bf:Place",
    }

    # test idref changes to other gnd
    place_gnd_data["pid"] = "TEST2"
    gnd_record_2 = PlaceGndRecord.create(
        data=place_gnd_data, dbcommit=True, reindex=True, delete_pid=False
    )
    assert gnd_record_2.pid == "TEST2"
    m_gnd_record_2, m_action = gnd_record_2.create_or_update_mef(
        dbcommit=True, reindex=True
    )
    assert m_action == {"4": Action.CREATE}
    assert "md5" in m_gnd_record_2
    assert _no_md5(m_gnd_record_2) == {
        "$schema": "https://mef.rero.ch/schemas/places_mef/mef-place-v0.0.1.json",
        "gnd": {"$ref": "https://mef.rero.ch/api/places/gnd/TEST2"},
        "pid": "4",
        "type": "bf:Place",
    }

    for identified_by in idref_record["identifiedBy"]:
        if identified_by.get("source") == "GND":
            identified_by["value"] = "(DE-101)TEST2"
    idref_record = idref_record.update(data=idref_record, dbcommit=True, reindex=True)

    PlaceMefRecord.flush_indexes()
    m_idref_record, m_action = idref_record.create_or_update_mef(
        dbcommit=True, reindex=True
    )
    assert m_action == {"1": Action.DELETE_ENTITY, "4": Action.REPLACE}
    assert "md5" in m_idref_record
    assert _no_md5(m_idref_record) == {
        "$schema": f"{SCHEMA_URL}/mef-place-v0.0.1.json",
        "idref": {"$ref": "https://mef.rero.ch/api/places/idref/271330163"},
        "gnd": {"$ref": "https://mef.rero.ch/api/places/gnd/TEST2"},
        "pid": "4",
        "type": "bf:Place",
    }
    m_gnd_record = PlaceMefRecord.get_record_by_pid(m_gnd_record.pid)
    assert "md5" in m_gnd_record
    assert _no_md5(m_gnd_record) == {
        "$schema": f"{SCHEMA_URL}/mef-place-v0.0.1.json",
        "gnd": {"$ref": "https://mef.rero.ch/api/places/gnd/TEST"},
        "pid": "1",
        "type": "bf:Place",
    }


def test_places_utils_get_place_endpoints(app):
    """Test get_place_endpoints utility function."""
    from rero_mef.places.utils import get_place_endpoints

    endpoints = get_place_endpoints()

    assert isinstance(endpoints, dict)
    # Should contain place endpoints
    assert "plgnd" in endpoints


def test_places_utils_get_place_classes(app):
    """get_place_classes returns record classes keyed by endpoint, without plmef by default."""
    from rero_mef.places.utils import get_place_classes

    classes = get_place_classes()
    assert isinstance(classes, dict)
    assert "plmef" not in classes
    assert "plgnd" in classes or "pidref" in classes

    classes_with_mef = get_place_classes(without_mef=False)
    assert isinstance(classes_with_mef, dict)
    assert len(classes_with_mef) >= len(classes)


def test_places_utils_make_identifier(app):
    """Test make_identifier utility function."""
    from rero_mef.places.utils import make_identifier

    # Test with source
    identified_by_with_source = {
        "type": "uri",
        "source": "IDREF",
        "value": "http://www.idref.fr/123456",
    }
    identifier = make_identifier(identified_by_with_source)
    assert identifier == "uri|(IDREF)http://www.idref.fr/123456"

    # Test without source
    identified_by_without_source = {"type": "bf:Isbn", "value": "978-3-16-148410-0"}
    identifier = make_identifier(identified_by_without_source)
    assert identifier == "bf:Isbn|978-3-16-148410-0"


def test_make_identifier(app):
    """make_identifier builds type|(source)value or type:value strings."""
    from rero_mef.places.utils import make_identifier

    assert make_identifier({"type": "bf:Nbn", "source": "GND", "value": "12345"}) == (
        "bf:Nbn|(GND)12345"
    )
    assert make_identifier({"type": "bf:Nbn", "value": "12345"}) == "bf:Nbn|12345"


def test_place_record_delete(app, place_idref_data):
    """PlaceRecord.delete removes the ref from linked MEF records."""
    from copy import deepcopy

    idref_record, _ = PlaceIdrefRecord.create_or_update(
        data=deepcopy(place_idref_data), dbcommit=True, reindex=True
    )
    m_record, _ = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_record.get("idref") is not None

    idref_record.delete(dbcommit=True, delindex=True)
    # The MEF record should have had the idref ref removed
    updated_mef = PlaceMefRecord.get_record_by_pid(m_record.pid)
    assert updated_mef is None or updated_mef.get("idref") is None
