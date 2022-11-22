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

from rero_mef.concepts import ConceptIdrefRecord, ConceptMefRecord, \
    ConceptReroRecord
from rero_mef.utils import export_json_records, number_records_in_file

SCHEMA_URL = 'https://mef.rero.ch/schemas/concepts_mef'


def test_create_concept_record(
        app, concept_rero_data,
        concept_idref_data, tmpdir):
    """Test create concept record with VIAF links."""
    idref_record, action = ConceptIdrefRecord.create_or_update(
        data=concept_idref_data, dbcommit=True, reindex=True)
    assert action.name == 'CREATE'
    assert idref_record['pid'] == '050548115'

    m_record, m_action = idref_record.create_or_update_mef(
        dbcommit=True, reindex=True)
    assert m_action.name == 'CREATE'
    assert m_record == {
        '$schema': f'{SCHEMA_URL}/mef-concept-v0.0.1.json',
        'idref': {'$ref': 'https://mef.rero.ch/api/concepts/idref/050548115'},
        'deleted': '2022-09-03T07:07:32.526780+00:00',
        'pid': '1'
    }

    rero_record, action = ConceptReroRecord.create_or_update(
        data=concept_rero_data, dbcommit=True, reindex=True)
    assert action.name == 'CREATE'
    assert rero_record['pid'] == 'A021001006'
    m_record, m_action = rero_record.create_or_update_mef(
        dbcommit=True, reindex=True)
    assert m_action.name == 'CREATE'
    assert m_record == {
        '$schema': f'{SCHEMA_URL}/mef-concept-v0.0.1.json',
        'rero': {'$ref': 'https://mef.rero.ch/api/concepts/rero/A021001006'},
        'pid': '2',
    }

    mef_rec_resolved = m_record.replace_refs()
    assert mef_rec_resolved.get('rero').get('pid') == rero_record.pid

    # Test JSON export.
    tmp_file_name = os.path.join(tmpdir, 'mef.json')
    export_json_records(
        pids=ConceptMefRecord.get_all_pids(),
        pid_type='comef',
        output_file_name=tmp_file_name,
    )
    assert number_records_in_file(tmp_file_name, 'json') == 2
    assert '$schema' in open(tmp_file_name).read()
    export_json_records(
        pids=ConceptMefRecord.get_all_pids(),
        pid_type='comef',
        output_file_name=tmp_file_name,
        schema=False
    )
    assert number_records_in_file(tmp_file_name, 'json') == 2
    assert '$schema' not in open(tmp_file_name).read()

    # Test update concept record.
    returned_record, action = ConceptReroRecord.create_or_update(
        data=concept_rero_data, dbcommit=True, reindex=True)
    assert action.name == 'UPDATE'
    assert returned_record['pid'] == 'A021001006'

    returned_record, action = ConceptIdrefRecord.create_or_update(
        data=concept_idref_data, dbcommit=True, reindex=True)
    assert action.name == 'UPDATE'
    assert returned_record['pid'] == '050548115'

    # Test update MD5 concept record MD5 tewst.
    returned_record, action = ConceptReroRecord.create_or_update(
        data=concept_rero_data, dbcommit=True, reindex=True, test_md5=True)
    assert action.name == 'UPTODATE'
    assert returned_record['pid'] == 'A021001006'

    returned_record, action = ConceptIdrefRecord.create_or_update(
        data=concept_idref_data, dbcommit=True, reindex=True, test_md5=True)
    assert action.name == 'UPTODATE'
    assert returned_record['pid'] == '050548115'
