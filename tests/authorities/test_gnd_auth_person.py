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
    assert trans.json == {}


def test_gnd_language_of_person():
    """Test language of person 377 $a (language 3 characters) ISO 639-2b"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="377">
            <subfield code="a">fre</subfield>
            <subfield code="a">eng</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_language_of_person()
    assert trans.json == {
        'language_of_person': [
            'fre',
            'eng'
        ]
    }


def test_gnd_language_of_person_missing():
    """Test language of person 377 missing"""
    xml_part_to_add = ""
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_language_of_person()
    assert trans.json == {}


def test_gnd_identifier_for_person():
    """Test identifier for person 001"""
    xml_part_to_add = """
       <controlfield tag="001">118577166</controlfield>
        <datafield ind1=" " ind2=" " tag="024">
            <subfield code="a">http://d-nb.info/gnd/100000193</subfield>
            <subfield code="2">uri</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_identifier_for_person()
    assert trans.json == {
        'identifier_for_person': 'http://d-nb.info/gnd/100000193',
        'pid': '118577166'
    }


def test_gnd_identifier_for_person_missing():
    """Test identifier for person 001 missing"""
    xml_part_to_add = ""
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_identifier_for_person()
    assert trans.json == {}


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
    assert trans.json == {}


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
    assert trans.json == {}


def test_gnd_preferred_name_for_person():
    """Test Preferred Name for Person 100 $a"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="a">Bauer, Johann Gottfried</subfield>
        </datafield>
     """
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_preferred_name_for_person()
    assert trans.json == {
        'preferred_name_for_person':
            'Bauer, Johann Gottfried'
    }


def test_gnd_preferred_name_for_person_missing():
    """Test Preferred Name for Person 100 $a missing"""
    xml_part_to_add = ""
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_preferred_name_for_person()
    assert trans.json == {}


def test_gnd_variant_name_for_person():
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
    trans.trans_gnd_variant_name_for_person()
    assert trans.json == {
        'variant_name_for_person': [
            'Barbanson, Konstantin von',
            'Barbanc\u0327on, Konstantyn'
        ]
    }


def test_gnd_variant_name_for_person_missing():
    """Test Variant Name for Person 400 $a missing"""
    xml_part_to_add = ""
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_variant_name_for_person()
    assert trans.json == {}


def test_gnd_authorized_access_point_representing_a_person():
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
    trans.trans_gnd_authorized_access_point_representing_a_person()
    assert trans.json == {
        'authorized_access_point_representing_a_person':
            'Johannes Paul, II., Papst, 1920-2005'
    }


def test_gnd_authorized_access_point_representing_a_person_missing():
    """Test Authorized access point representing a person 100 $abcd missing
    """
    xml_part_to_add = ""
    trans = trans_prep('gnd', xml_part_to_add)
    trans.trans_gnd_authorized_access_point_representing_a_person()
    assert trans.json == {}
