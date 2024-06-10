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

"""Test places api."""

import os

from rero_mef.api import Action
from rero_mef.places import PlaceIdrefRecord, PlaceMefRecord
from rero_mef.utils import export_json_records, number_records_in_file

SCHEMA_URL = "https://mef.rero.ch/schemas/places_mef"


def test_create_place_record(app, place_idref_data, tmpdir):
    """Test create place record with VIAF links."""
    idref_record, action = PlaceIdrefRecord.create_or_update(
        data=place_idref_data, dbcommit=True, reindex=True
    )
    assert action == Action.CREATE
    assert idref_record["pid"] == "271330163"

    m_record, m_action = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert action == Action.CREATE
    assert m_record == {
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

    # Test update MD5 place record MD5 tewst.
    returned_record, action = PlaceIdrefRecord.create_or_update(
        data=place_idref_data, dbcommit=True, reindex=True, test_md5=True
    )
    assert action == Action.UPTODATE
    assert returned_record["pid"] == "271330163"
