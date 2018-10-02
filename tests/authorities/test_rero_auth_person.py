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

"""Test RERO auth person."""

from helpers import trans_prep


def test_rero_identifier_for_person():
    """Test identifier for person 035"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="035">
            <subfield code="a">A000070488</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_identifier_for_person()
    assert trans.json == {
        'pid': 'A000070488',
        'identifier_for_person': 'http://data.rero.ch/02-A000070488'
    }


def test_rero_birth_and_death_dates():
    """Test date of birth 100 $d"""
    xml_part_to_add = ""
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_birth_and_death_dates()
    assert trans.json == {}

    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="d">1816-1855</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '1816',
        'date_of_death': '1855'
    }
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="d">1816-</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '1816'
    }

    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="d">?-1855</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '?',
        'date_of_death': '1855'
    }

    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="d">ca. 1800-1855</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': 'ca. 1800',
        'date_of_death': '1855'
    }


def test_rero_biographical_information():
    """Test biographical information 680 $a"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="680">
            <subfield code="a">Romancière. - Charlotte Brontë.</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_biographical_information()
    assert trans.json == {
        'biographical_information': [
            'Romancière. - Charlotte Brontë.'
        ]
    }


def test_rero_preferred_name_for_person():
    """Test Preferred Name for Person 100 $a"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="a">Brontë, Charlotte</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_preferred_name_for_person()
    assert trans.json == {
        'preferred_name_for_person':
            'Brontë, Charlotte'
    }


def test_rero_variant_name_for_person():
    """Test Variant Name for Person 400 $a"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="400">
            <subfield code="a">Bell, Currer:</subfield>
        </datafield>
         <datafield ind1=" " ind2=" " tag="400">
            <subfield code="a">Brontë, Carlotta ,</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_variant_name_for_person()
    assert trans.json == {
        'variant_name_for_person': [
            'Bell, Currer',
            'Brontë, Carlotta'
        ]
    }


def test_rero_authorized_access_point_representing_a_person():
    """Test Authorized access point representing a person 100 $adc"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="a">Brontë, Charlotte,</subfield>
            <subfield code="d">1816-1855</subfield>
            <subfield code="c">écrivain</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_authorized_access_point_representing_a_person()
    assert trans.json == {
        'authorized_access_point_representing_a_person':
            'Brontë, Charlotte, 1816-1855, écrivain'
    }

    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="a">Paul</subfield>
            <subfield code="b">VI</subfield>
            <subfield code="c">pape</subfield>
            <subfield code="d">1897-1978</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_authorized_access_point_representing_a_person()
    assert trans.json == {
        'authorized_access_point_representing_a_person':
            'Paul, VI, pape, 1897-1978'
    }
