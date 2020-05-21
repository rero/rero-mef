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

"""Test IDREF auth person."""

from helpers import trans_prep


def test_idref_gender_female():
    """Test gender 120 $a a = female, b = male, - = not known."""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="120">
            <subfield code="a">a</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_gender()
    assert trans.json == {
        'gender': 'female'
    }


def test_idref_gender_male():
    """Test gender 120 $a a = female, b = male, - = not known."""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="120">
            <subfield code="a">b</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_gender()
    assert trans.json == {
        'gender': 'male'
    }


def test_idref_gender_missing():
    """Test gender 120 missing"""
    xml_part_to_add = ""
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_gender()
    assert not trans.json


def test_idref_language_of_person():
    """Test language of person 101 $a (language 3 characters) ISO 639-2"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="101">
            <subfield code="a">fre</subfield>
            <subfield code="a">eng</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_language_of_person()
    assert trans.json == {
        'language_of_person': [
            'fre',
            'eng'
        ]
    }


def test_idref_language_of_perso__missing():
    """Test language of person 101 missing"""
    xml_part_to_add = ""
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_language_of_person()
    assert not trans.json


def test_idref_identifier_for_person():
    """Test identifier for person"""
    xml_part_to_add = """
        <controlfield
        tag="003">http://www.idref.fr/069774331</controlfield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_identifier_for_person()
    assert trans.json == {
        'identifier_for_person': 'http://www.idref.fr/069774331'
    }


def test_idref_identifier_for_person_missing():
    """Test identifier for person 001 missing"""
    xml_part_to_add = ""
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_identifier_for_person()
    assert not trans.json


def test_idref_pid():
    """Test pid for person"""
    xml_part_to_add = """
        <controlfield tag="001">069774331</controlfield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_pid()
    assert trans.json == {'pid': '069774331'}


def test_idref_birth_and_death_from_field_103():
    """Test date of birth 103 $a pos. 1-8 YYYYMMDD"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="103">
            <subfield code="a">18160421</subfield>
            <subfield code="b">18550331</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '1816-04-21',
        'date_of_death': '1855-03-31'
    }

    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="103">
            <subfield code="a">18160421</subfield>
            <subfield code="b">1855</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '1816-04-21',
        'date_of_death': '1855'
    }


def test_idref_birth_and_death_dates_year_birth():
    """Test date of birth 103 $a pos. 1-8 YYYYMMDD"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="103">
            <subfield code="a">1816?</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '1816?'
    }


def test_idref_birth_and_death_from_field_200():
    """Test date of birth 200 $f pos. 1-4"""
    xml_part_to_add = """
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">1816-1855</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '1816',
        'date_of_death': '1855'
    }

    #  format: "XX.. ?-XX.. ?"
    xml_part_to_add = """
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">18.. ?-19.. ?</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '18..?',
        'date_of_death': '19..?'
    }

    #  format: "XXXX-XXXX?"
    xml_part_to_add = """
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">1812-1918?</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '1812',
        'date_of_death': '1918?'
    }

    #  format: "XX..-XXXX?"
    xml_part_to_add = """
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">18..-1918?</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '18..',
        'date_of_death': '1918?'
    }

    #  format: "XX..-"
    xml_part_to_add = """
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">18..-</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '18..'
    }

    #  format: "-XXXX?"
    xml_part_to_add = """
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">-1961?</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {
        'date_of_death': '1961?'
    }

    #  format: "XXXX"
    xml_part_to_add = """
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">1961</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '1961'
    }


def test_idref_birth_and_death_dates_in_two_fields():
    """Test date of birth 103 $a pos. 1-8 YYYYMMDD AND 200 $f pos. 1-4"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="103">
            <subfield code="a">18160421</subfield>
            <subfield code="b">18550331</subfield>
        </datafield>
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">1816-1855</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '1816-04-21',
        'date_of_death': '1855-03-31'
    }

    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="103">
            <subfield code="a">1525</subfield>
            <subfield code="b">16010723</subfield>
        </datafield>
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">1525?-1601</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '1525',
        'date_of_death': '1601-07-23'
    }

    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="103">
            <subfield code="a">1525</subfield>
            <subfield code="b">16010723</subfield>
        </datafield>
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">1525?-1601</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {
        'date_of_birth': '1525',
        'date_of_death': '1601-07-23'
    }


def test_idref_birth_and_death_dates_missing():
    """Test date of birth 103 AND 200 missing"""
    xml_part_to_add = ""
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert not trans.json


def test_idref_biographical_information():
    """Test biographical information 300 $a 34x $a"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="300">
            <subfield code="a">Giacomo Nicolini da Sabbio.</subfield>
        </datafield>
        <datafield ind1=" " ind2=" " tag="341">
            <subfield code="a">Venezia</subfield>
            <subfield code="a">Italia</subfield>
        </datafield>
        <datafield ind1=" " ind2=" " tag="350">
            <subfield code="a">ignorer</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_biographical_information()
    assert trans.json == {
        'biographical_information': [
            'Giacomo Nicolini da Sabbio.',
            'Venezia, Italia'
        ]
    }


def test_idref_biographical_information_missing():
    """Test biographical information 300 $a 34x $a. missing"""
    xml_part_to_add = ""
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_biographical_information()
    assert not trans.json


def test_idref_preferred_name_for_person_1():
    """Test Preferred Name for Person 200 $ab"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="200">
            <subfield code="a">Brontë</subfield>
            <subfield code="b">Charlotte</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_preferred_name_for_person()
    assert trans.json == {
        'preferred_name_for_person':
            'Brontë, Charlotte'
    }


def test_idref_preferred_name_for_person_missing():
    """Test Preferred Name for Person 200 $ab missing"""
    xml_part_to_add = ""
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_preferred_name_for_person()
    assert not trans.json


def test_idref_preferred_name_for_person_missing():
    """Test Preferred Name for Person 100 $a missing"""
    xml_part_to_add = ""
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_preferred_name_for_person()
    assert not trans.json


def test_trans_idref_numeration():
    """Test numeration for Person 200 $d"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="200">
            <subfield code="d">II</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_numeration()
    assert trans.json == {
        'numeration':
            'II'
    }


def test_trans_idref_qualifier():
    """Test numeration for Person 200 $c"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="200">
            <subfield code="c">Jr.</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_qualifier()
    assert trans.json == {
        'qualifier':
            'Jr.'
    }


def test_idref_variant_name_for_person():
    """Test Variant Name for Person 400 $ab"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="400">
            <subfield code="a">Bell</subfield>
            <subfield code="b">Currer</subfield>
        </datafield>
         <datafield ind1=" " ind2=" " tag="400">
            <subfield code="a">Brontë</subfield>
            <subfield code="b">Carlotta</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_variant_name_for_person()
    assert trans.json == {
        'variant_name_for_person': [
            'Bell, Currer',
            'Brontë, Carlotta'
        ]
    }


def test_idref_variant_name_for_person_missing():
    """Test Variant Name for Person 400 $ab missing"""
    xml_part_to_add = ""
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_variant_name_for_person()
    assert not trans.json


def test_idref_authorized_access_point_representing_a_person():
    """Test Authorized access point representing a person 200 $abcdf"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="200">
            <subfield code="a">Brontë</subfield>
            <subfield code="b">Charlotte</subfield>
            <subfield code="c">écrivain</subfield>
            <subfield code="c">biographe</subfield>
            <subfield code="f">1816-1855</subfield>
            <subfield code="e">ignorer</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_authorized_access_point_representing_a_person()
    assert trans.json == {
        'authorized_access_point_representing_a_person':
            'Brontë, Charlotte, écrivain, biographe, 1816-1855'
    }


def test_idref_authorized_access_point_representing_a_person_missing():
    """Test Authorized access point representing a person 200 $abcdf missing"""
    xml_part_to_add = ""
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_authorized_access_point_representing_a_person()
    assert not trans.json


def test_authorized_access_point_representing_a_person_diff_order():
    """Test Authorized access point representing a person 200 $abdfc"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">1816-1855</subfield>
            <subfield code="b">Charlotte</subfield>
            <subfield code="a">Brontë</subfield>
            <subfield code="e">ignorer le texte</subfield>
            <subfield code="c">écrivain</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_authorized_access_point_representing_a_person()
    assert trans.json == {
        'authorized_access_point_representing_a_person':
            '1816-1855, Charlotte, Brontë, écrivain'
    }


def test_authorized_access_point_representing_a_person_general_order():
    """Test Authorized access point representing a person 200 $abdfc"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="200">
            <subfield code="a">Brontë</subfield>
            <subfield code="b">Charlotte</subfield>
            <subfield code="f">1816-1855</subfield>
            <subfield code="c">écrivain</subfield>
            <subfield code="e">ignorer le texte</subfield>
        </datafield>
     """
    trans = trans_prep('idref', xml_part_to_add)
    trans.trans_idref_authorized_access_point_representing_a_person()
    assert trans.json == {
        'authorized_access_point_representing_a_person':
            'Brontë, Charlotte, 1816-1855, écrivain'
    }
