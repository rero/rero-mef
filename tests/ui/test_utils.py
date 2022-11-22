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

"""Views tests."""

from __future__ import absolute_import, print_function

import os

from rero_mef.agents import AgentMefRecord
from rero_mef.concepts import ConceptMefRecord
from rero_mef.utils import JsonWriter, get_mefs_endpoints, \
    number_records_in_file, read_json_record


def test_get_mefs_endpoints(app):
    """Test get MEF endpoints."""
    endpoints = get_mefs_endpoints()
    assert endpoints[0]['mef_class'] == AgentMefRecord
    assert endpoints[1]['mef_class'] == ConceptMefRecord


def test_json_writer(tmpdir):
    """Test JsonWriter."""
    temp_file_name = os.path.join(tmpdir, 'test.json')
    with JsonWriter(temp_file_name) as temp_file:
        temp_file.write({'pid': '1'})
        temp_file.write({'pid': '2'})
    assert number_records_in_file(temp_file_name, 'json') == 2
    for idx, record in enumerate(read_json_record(open(temp_file_name)), 1):
        assert record.get('pid') == str(idx)
