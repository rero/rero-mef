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

"""Test marctojson helper."""

from pymarc import Field, Record

from rero_mef.marctojson.helper import build_string_list_from_fields


def test_build_string_list_from_fields():
    """Test build_string_list_from_fields."""
    record = Record()
    record.add_field(
        Field(
            tag='200',
            indicators=['0', '1'],
            subfields=[
                'a', 'Cerasi',
                'b', 'Claudio et Elena',
                'x', "Collections d'art"
            ]))
    data = build_string_list_from_fields(
        record=record,
        tag='200',
        subfields={'a': ', ', 'b': ', ', 'c': ', ', 'd': ', ', 'f': ', ',
                   'x': ' - '}
    )
    assert data == ["Cerasi, Claudio et Elena - Collections d'art"]

    record = Record()
    record.add_field(
        Field(
            tag='210',
            indicators=['0', '1'],
            subfields=[
                'a', 'Place of public./distr.',
                'b', 'Address/publisher/dist.',
                'c', 'Name of publisher/dist.',
                'd', 'Date',
                'e', 'Place',
                'f', 'Address'
            ]))
    data = build_string_list_from_fields(
        record=record,
        tag='210',
        subfields={'a': ', ', 'b': '. ', 'c': ', ', 'd': '; ', 'e': '; ',
                   'f': '; '},
        tag_grouping=[
            {
                'subtags': 'c',
                'start': ' ( ',
                'end': ' )',
                'delimiter': '',
                'subdelimiter': ', '
            },
            {
                'subtags': 'def',
                'start': ' ( ',
                'end': ' )',
                'delimiter': '',
                'subdelimiter': '; '
            }
        ]
    )
    assert data == [
        'Place of public./distr.'
        '. Address/publisher/dist.'
        ' ( Name of publisher/dist. )'
        ' ( Date; Place; Address )'
    ]
