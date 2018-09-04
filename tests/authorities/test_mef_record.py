# -*- coding: utf-8 -*-
#
# This file is part of RERO MEF.
# Copyright (C) 2018 RERO.
#
# RERO MEF is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO MEF is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO MEF; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Test MEF record."""

from rero_mef.authorities.marctojson.mef_record import MEF_record


def test_mef_record_bnf(empty_mef_record):
    """Test andding a JSON source data for BNF."""
    mef_record = MEF_record(
        json_data=empty_mef_record,
        logger=None,
        verbose=False
    )
    json_data = {}
    json_data['gender'] = 'female'

    mef_record.update_source(source='bnf', json_data=json_data)
    assert mef_record.json == {
        "md5": [
            {'source': 'bnf', 'value': '875a47ddcf63e33a4d5f65db190e73d0'}
        ],
        "gender": [
            {
                'source': 'bnf',
                'value': 'female'
            }
        ]
    }


def test_mef_record_bnf_gnd(empty_mef_record):
    """Test andding a JSON source data for BNF and GND."""
    mef_record = MEF_record(
        json_data=empty_mef_record,
        logger=None,
        verbose=False
    )
    bnf_json_data = {}
    bnf_json_data['gender'] = 'female'
    gnd_json_data = {}
    gnd_json_data['gender'] = 'female'

    mef_record.update_source(source='bnf', json_data=bnf_json_data)
    mef_record.update_source(source='gnd', json_data=gnd_json_data)
    assert mef_record.json == {
        "md5": [
            {'source': 'bnf', 'value': '875a47ddcf63e33a4d5f65db190e73d0'},
            {'source': 'gnd', 'value': '875a47ddcf63e33a4d5f65db190e73d0'}
        ],
        "gender": [
            {
                'source': 'bnf',
                'value': 'female'
            },
            {
                'source': 'gnd',
                'value': 'female'
            },
        ]
    }
    new_bnf_json_data = {}
    new_bnf_json_data['gender'] = 'male'
    mef_record.update_source(source='bnf', json_data=new_bnf_json_data)
    assert mef_record.json == {
        "md5": [
            {'source': 'gnd', 'value': '875a47ddcf63e33a4d5f65db190e73d0'},
            {'source': 'bnf', 'value': 'fee8baae9d07f5e237693ddd9137b8c8'}
        ],
        "gender": [
            {
                'source': 'gnd',
                'value': 'female'
            },
            {
                'source': 'bnf',
                'value': 'male'
            }
        ]
    }


def test_mef_record_add_remove(empty_mef_record):
    """Test andding and removing source data."""
    mef_record = MEF_record(
        json_data=empty_mef_record,
        logger=None,
        verbose=False
    )
    bnf_json_data = {}
    bnf_json_data['gender'] = 'female'
    gnd_json_data = {}
    gnd_json_data['gender'] = 'female'
    mef_record.update_source(source='bnf', json_data=bnf_json_data)
    mef_record.update_source(source='gnd', json_data=gnd_json_data)
    mef_record.delete_source(source='bnf')
    assert mef_record.json == {
        "md5": [
            {'source': 'gnd', 'value': '875a47ddcf63e33a4d5f65db190e73d0'}
        ],
        "gender": [
            {
                'source': 'gnd',
                'value': 'female'
            },
        ]
    }
