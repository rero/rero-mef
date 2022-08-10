# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2021 RERO
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

"""Test api."""

from rero_mef.concepts.mef.api import ConceptMefRecord
from rero_mef.concepts.tasks import task_create_mef_for_concept


def test_task_create_mef_for_concept(
        app, concept_rero_record, concept_idref_record):
    """Test ReroMefRecord api."""
    corero = concept_rero_record
    assert task_create_mef_for_concept('XXXX', 'corero') == \
        'Not found concept corero:XXXX'
    assert task_create_mef_for_concept(corero.pid, 'corero') == \
        'Create MEF from corero pid: A021001006 | mef: 1 create'
    mef = ConceptMefRecord.get_record_by_pid('1')
    assert mef == {
        '$schema':
            'https://mef.rero.ch/schemas/concepts_mef/mef-concept-v0.0.1.json',
            'pid': '1',
            'rero': {
                '$ref': f'https://mef.rero.ch/api/concepts/rero/{corero.pid}'}
    }
    cidref = concept_idref_record
    assert task_create_mef_for_concept('XXXX', 'cidref') == \
        'Not found concept cidref:XXXX'
    assert task_create_mef_for_concept(cidref.pid, 'cidref') == \
        f'Create MEF from cidref pid: {cidref.pid} | mef: 2 create'
    mef = ConceptMefRecord.get_record_by_pid('2')
    assert mef == {
        '$schema':
            'https://mef.rero.ch/schemas/concepts_mef/mef-concept-v0.0.1.json',
            'pid': '2',
            'idref': {
                '$ref': f'https://mef.rero.ch/api/concepts/idref/{cidref.pid}'}
    }
