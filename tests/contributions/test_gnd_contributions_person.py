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

"""Test GND auth person."""

from helpers import trans_prep


def test_gnd_deleted():
    """Test deleted -> leader 6 == d."""
    xml_part_to_add = """
        <leader>00000nz  a2200000oc 4500</leader>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_deleted()
    assert not trans.json

    xml_part_to_add = """
        <leader>00000cz  a2200000oc 4500</leader>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_deleted()
    assert 'deleted' in trans.json

    xml_part_to_add = """
        <leader>00000xz  a2200000oc 4500</leader>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_deleted()
    assert 'deleted' in trans.json

    xml_part_to_add = """
        <leader>00000dz  a2200000oc 4500</leader>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_deleted()
    assert 'deleted' in trans.json


def test_gnd_relation_pid():
    """Test new pid 682 $0 $i == 'Umlenkung'."""
    xml_part_to_add = """
        <datafield tag="682" ind1=" " ind2=" ">
            <subfield code="i">Umlenkung</subfield>
            <subfield code="0">(DE-101)100937187</subfield>
            <subfield code="0">(DE-588)100937187</subfield>
            <subfield code="0">https://d-nb.info/gnd/100937187</subfield>
            <subfield code="a">Albericus, Londoniensis</subfield>
        </datafield>
    """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_relation_pid()
    assert trans.json == {'relation_pid': {
        'value': '100937187',
        'type': 'redirect_to'
    }}


def test_gnd_gender_female():
    """Test gender 375 $a 1 = male, 2 = female, " " = not known."""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="375">
            <subfield code="a">2</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_gender()
    assert trans.json == {
        'gender': 'female'
    }


def test_gnd_gender_male():
    """Test gender 375 $a 1 = male, 2 = female, " " = not known."""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="375">
            <subfield code="a">1</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_gender()
    assert trans.json == {
        'gender': 'male'
    }


def test_gnd_gender_missing():
    """Test gender 375 missing"""
    xml_part_to_add = ""
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_gender()
    assert not trans.json


def test_gnd_language():
    """Test language of person 377 $a (language 3 characters) ISO 639-2b"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="377">
            <subfield code="a">fre</subfield>
            <subfield code="a">eng</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_language()
    assert trans.json == {
        'language': [
            'fre',
            'eng'
        ]
    }


def test_gnd_language_missing():
    """Test language of person 377 missing"""
    xml_part_to_add = ""
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_language()
    assert not trans.json


def test_gnd_identifier():
    """Test identifier for person 001"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="024">
            <subfield code="0">http://d-nb.info/gnd/100000193</subfield>
            <subfield code="2">gnd</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_identifier()
    assert trans.json == {
        'identifier': 'http://d-nb.info/gnd/100000193',
    }


def test_gnd_identifier_missing():
    """Test identifier for person 001 missing"""
    xml_part_to_add = ""
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_identifier()
    assert not trans.json


def test_gnd_pid():
    """Test pid for person"""
    xml_part_to_add = """
        <controlfield tag="001">118577166</controlfield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_pid()
    assert trans.json == {
        'pid': '118577166',
    }


def test_gnd_birth_and_death_dates_year_birth_death():
    """Test date of birth 100 $d YYYY-YYYY"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="d">1816-1855</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '1816',
        'date_of_death': '1855'
    }


def test_gnd_birth_and_death_dates_year_birth():
    """Test date of birth 100 $d YYYY-"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="d">1816-</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '1816'
    }


def test_gnd_birth_and_death_dates_year_death():
    """Test date of birth 100 $d -YYYY"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="d">-1855</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_birth_and_death_dates()
    assert trans.json == {
        'date_of_death': '1855'
    }


def test_gnd_birth_and_death_dates_birth_death_date():
    """Test date of birth 548 $a DD.MM.YYYY-DD.MM.YYYY $4 datx"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="548">
            <subfield code="a">06.06.1875-12.08.1955</subfield>
            <subfield code="4">datx</subfield>
        </datafield>
        <datafield ind1=" " ind2=" " tag="548">
            <subfield code="a">1875-1955</subfield>
            <subfield code="4">datl</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '06.06.1875',
        'date_of_death': '12.08.1955'
    }


def test_gnd_birth_and_death_dates_birth_date_completed():
    """Test date of birth 548 $a DD.MM.YYYY-DD.MM.YYYY $4 datx"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="548">
            <subfield code="a">-26.11.1631</subfield>
            <subfield code="4">datx</subfield>
        </datafield>
        <datafield ind1=" " ind2=" " tag="548">
            <subfield code="a">1582-1631</subfield>
            <subfield code="4">datl</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '1582',
        'date_of_death': '26.11.1631'
    }


def test_gnd_birth_and_death_dates_birth():
    """Test date of birth 548 $a DD.MM.YYYY- $4 datx"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="548">
          <subfield code="a">06.06.1875-</subfield>
          <subfield code="4">datx</subfield>
        </datafield>
        <datafield ind1=" " ind2=" " tag="548">
            <subfield code="a">1875-</subfield>
            <subfield code="4">datl</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '06.06.1875'
    }


def test_gnd_birth_and_death_dates_death():
    """Test date of birth 548 $a -DD.MM.YYYY $4 datx"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="548">
          <subfield code="a">-12.08.1955</subfield>
          <subfield code="4">datx</subfield>
        </datafield>
        <datafield ind1=" " ind2=" " tag="548">
            <subfield code="a">-1955</subfield>
            <subfield code="4">datl</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_birth_and_death_dates()
    assert trans.json == {
        'date_of_death': '12.08.1955'
    }


def test_gnd_birth_and_death_dates_missing():
    """Test date of birth 100 AND 548 missing"""
    xml_part_to_add = ""
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_birth_and_death_dates()
    assert not trans.json


def test_gnd_biographical_information():
    """Test biographical information 670 $abu"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="678">
            <subfield code="a">Dizionario Biografico (1960)</subfield>
            <subfield code="b">Camillo</subfield>
    <subfield code="u">treccani.it/enc</subfield>
        </datafield>
         <datafield ind1=" " ind2=" " tag="678">
            <subfield code="b">Dt. Franziskaner-Minorit</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_biographical_information()
    assert trans.json == {
        'biographical_information': [
            'Dizionario Biografico (1960), Camillo, treccani.it/enc',
            'Dt. Franziskaner-Minorit'
        ]
    }


def test_gnd_biographical_information_missing():
    """Test biographical information 678 missing"""
    xml_part_to_add = ""
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_biographical_information()
    assert not trans.json


def test_gnd_preferred_name():
    """Test Preferred Name for Person 100 $a"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="a">Bauer, Johann Gottfried</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_preferred_name()
    assert trans.json == {'preferred_name': 'Bauer, Johann Gottfried'}


def test_gnd_preferred_name_missing():
    """Test Preferred Name for Person 100 $a missing"""
    xml_part_to_add = ""
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_preferred_name()
    assert not trans.json


def test_trans_gnd_numeration():
    """Test numeration for Person 100 $b"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="b">II</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_numeration()
    assert trans.json == {
        'numeration':
            'II'
    }


def test_trans_gnd_qualifier():
    """Test numeration for Person 100 $c"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="c">Jr.</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_qualifier()
    assert trans.json == {
        'qualifier':
            'Jr.'
    }


def test_gnd_variant_name():
    """Test Variant Name for Person 400 $a"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="400">
            <subfield code="a">Barbanson</subfield>
            <subfield code="c">Konstantin \u0098von\u009c</subfield>
        </datafield>
         <datafield ind1=" " ind2=" " tag="400">
            <subfield code="a">Barbanc\u0327on</subfield>
            <subfield code="c">Konstantyn</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_variant_name()
    assert trans.json == {
        'variant_name': [
            'Barbanson, Konstantin von',
            'Barbanc\u0327on, Konstantyn'
        ]
    }


def test_gnd_variant_name_missing():
    """Test Variant Name for Person 400 $a missing"""
    xml_part_to_add = ""
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_variant_name()
    assert not trans.json


def test_gnd_authorized_access_point():
    """Test Authorized access point representing a person 100 $abcd"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="a">Johannes Paul</subfield>
            <subfield code="b">II.</subfield>
            <subfield code="c">Papst</subfield>
            <subfield code="d">1920-2005</subfield>
            <subfield code="g">Sonstige Info.</subfield>
            <subfield code="t">Ad tuendam fidem</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_authorized_access_point()
    assert trans.json == {
        'authorized_access_point': 'Johannes Paul, II., Papst, 1920-2005',
        'bf:Agent': 'bf:Person'
    }


def test_gnd_authorized_access_point_missing():
    """Test Authorized access point representing a person 100 $abcd missing
    """
    xml_part_to_add = ""
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_authorized_access_point()
    assert not trans.json
