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

"""Test RERO auth agent."""

from agents_helpers import trans_prep


def test_rero_identifier():
    """Test identifier for person 035"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="035">
            <subfield code="a">A000070488</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_identifier()
    assert trans.json == {
        'pid': 'A000070488',
        'identifier': 'http://data.rero.ch/02-A000070488',
        'identifiedBy': [{
            'source': 'RERO',
            'type': 'uri',
            'value': 'http://data.rero.ch/02-A000070488'
        }]
    }


def test_rero_birth_and_death_dates():
    """Test date of birth 100 $d"""
    xml_part_to_add = ""
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_birth_and_death_dates()
    assert not trans.json

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


def test_rero_preferred_name():
    """Test Preferred Name for Person 100 $a"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="a">Brontë, Charlotte</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_preferred_name()
    assert trans.json == {'preferred_name': 'Brontë, Charlotte'}


def test_rero_preferred_name_organisation():
    """Test Preferred Name for Person 110 $a"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="110">
            <subfield code="a">Brontë, Charlotte</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_preferred_name()
    assert trans.json == {'preferred_name': 'Brontë, Charlotte'}


def test_trans_rero_numeration():
    """Test numeration for Person 100 $b"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="b">II</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_numeration()
    assert trans.json == {
        'numeration':
            'II'
    }


def test_trans_rero_qualifier():
    """Test numeration for Person 100 $c"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="c">Jr.</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_qualifier()
    assert trans.json == {'qualifier': 'Jr.'}


def test_rero_variant_name():
    """Test Variant Name for Person 400 $a"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="400">
            <subfield code="a">Bell, Currer</subfield>
        </datafield>
         <datafield ind1=" " ind2=" " tag="400">
            <subfield code="a">Brontë, Carlotta</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_variant_name()
    trans.trans_rero_variant_access_point()
    assert trans.json == {
        'variant_access_point': ['Bell, Currer', 'Brontë, Carlotta'],
        'variant_name': ['Bell, Currer', 'Brontë, Carlotta']
    }
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="410">
            <subfield code="a">Bell, Currer</subfield>
        </datafield>
         <datafield ind1=" " ind2=" " tag="410">
            <subfield code="a">Brontë, Carlotta</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_variant_name()
    trans.trans_rero_variant_access_point()
    assert trans.json == {
        'variant_access_point': ['Bell, Currer', 'Brontë, Carlotta'],
        'variant_name': ['Bell, Currer', 'Brontë, Carlotta']
    }
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="411">
            <subfield code="a">Bell, Currer</subfield>
        </datafield>
         <datafield ind1=" " ind2=" " tag="411">
            <subfield code="a">Brontë, Carlotta</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_variant_name()
    trans.trans_rero_variant_access_point()


def test_rero_authorized_access_point():
    """Test Authorized access point representing a person 100 $adc"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="a">Brontë, Charlotte,</subfield>
            <subfield code="d">1816-1855</subfield>
            <subfield code="c">écrivain</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_authorized_access_point()
    assert trans.json == {
        'authorized_access_point': 'Brontë, Charlotte, 1816-1855 écrivain',
        'bf:Agent': 'bf:Person'
    }

    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="110">
            <subfield code="a">Paul</subfield>
            <subfield code="b">VI</subfield>
            <subfield code="c">pape</subfield>
            <subfield code="d">1897-1978</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_authorized_access_point()
    assert trans.json == {
        'authorized_access_point': 'Paul VI pape 1897-1978',
        'bf:Agent': 'bf:Organisation',
        'conference': False,
    }


def test_rero_parallel_access_point():
    """Test parallel access point 700/710/710."""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="700">
            <subfield code="a">Brontë, Charlotte,</subfield>
            <subfield code="d">1816-1855</subfield>
            <subfield code="c">écrivain</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_parallel_access_point()
    assert trans.json == {
        'parallel_access_point': ['Brontë, Charlotte, 1816-1855 écrivain']
    }

    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="710">
            <subfield code="a">Paul</subfield>
            <subfield code="b">VI</subfield>
            <subfield code="c">pape</subfield>
            <subfield code="d">1897-1978</subfield>
        </datafield>
     """
    trans = trans_prep('rero', xml_part_to_add)
    trans.trans_rero_parallel_access_point()
    assert trans.json == {'parallel_access_point': ['Paul VI pape 1897-1978']}
