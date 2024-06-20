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

"""Test IDREF auth person."""

from agents_helpers import trans_prep


def test_idref_deleted():
    """Test deleted -> leader 6 == d."""
    xml_part_to_add = """
        <leader>     dx  a22     3  45  </leader>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_deleted()
    assert "deleted" in trans.json

    xml_part_to_add = """
        <leader>     cx  a22     3  45  </leader>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_deleted()
    assert not trans.json


def test_idref_relation_pid():
    """Test old pids 035 $a $9 == 'sudoc'."""
    xml_part_to_add = """
        <datafield tag="035" ind1=" " ind2=" ">
            <subfield code="a">027630501</subfield>
            <subfield code="9">sudoc</subfield>
        </datafield>
        <datafield tag="035" ind1=" " ind2=" ">
            <subfield code="a">frBN001940328</subfield>
        </datafield>
        <datafield tag="035" ind1=" " ind2=" ">
            <subfield code="a">frBN000000089</subfield>
        </datafield>
        <datafield tag="035" ind1=" " ind2=" ">
            <subfield code="a">FRBNF118620892</subfield>
            <subfield code="z">FRBNF11862089</subfield>
        </datafield>
        <datafield tag="035" ind1=" " ind2=" ">
            <subfield code="a">http://viaf.org/viaf/124265140</subfield>
            <subfield code="2">VIAF</subfield>
            <subfield code="C">VIAF</subfield>
            <subfield code="d">20200302</subfield>
        </datafield>
        <datafield tag="035" ind1=" " ind2=" ">
            <subfield code="a">A003915957</subfield>
            <subfield code="2">RERO</subfield>
        </datafield>
    """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_relation_pid()
    assert trans.json == {
        "identifiedBy": [
            {
                "source": "VIAF",
                "type": "uri",
                "value": "http://viaf.org/viaf/124265140",
            },
            {"source": "RERO", "type": "bf:Nbn", "value": "A003915957"},
        ],
        "relation_pid": {"value": "027630501", "type": "redirect_from"},
    }


def test_idref_gender_female():
    """Test gender 120 $a a = female, b = male, - = not known."""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="120">
            <subfield code="a">a</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_gender()
    assert trans.json == {"gender": "female"}


def test_idref_gender_male():
    """Test gender 120 $a a = female, b = male, - = not known."""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="120">
            <subfield code="a">b</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_gender()
    assert trans.json == {"gender": "male"}


def test_idref_gender_unknown():
    """Test gender 120 $a a = female, b = male, - = not known."""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="120">
            <subfield code="a">-</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_gender()
    assert trans.json == {"gender": "not known"}


def test_idref_gender_missing():
    """Test gender 120 missing"""
    xml_part_to_add = ""
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_gender()
    assert not trans.json


def test_idref_language():
    """Test language of person 101 $a (language 3 characters) ISO 639-2"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="101">
            <subfield code="a">fre</subfield>
            <subfield code="a">eng</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_language()
    assert trans.json == {"language": ["fre", "eng"]}


def test_idref_language_of_perso__missing():
    """Test language of person 101 missing"""
    xml_part_to_add = ""
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_language()
    assert not trans.json


def test_idref_identifier():
    """Test identifier for person"""
    xml_part_to_add = """
        <controlfield
        tag="003">http://www.idref.fr/069774331</controlfield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_identifier()
    assert trans.json == {
        "identifier": "http://www.idref.fr/069774331",
        "identifiedBy": [
            {"source": "IDREF", "type": "uri", "value": "http://www.idref.fr/069774331"}
        ],
    }


def test_idref_identifier_missing():
    """Test identifier for person 001 missing"""
    xml_part_to_add = ""
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_identifier()
    assert not trans.json


def test_idref_pid():
    """Test pid for person"""
    xml_part_to_add = """
        <controlfield tag="001">069774331</controlfield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_pid()
    assert trans.json == {"pid": "069774331"}


def test_idref_birth_and_death_from_field_103():
    """Test date of birth 103 $a pos. 1-8 YYYYMMDD"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="103">
            <subfield code="a">18160421</subfield>
            <subfield code="b">18550331</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {"date_of_birth": "1816-04-21", "date_of_death": "1855-03-31"}

    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="103">
            <subfield code="a">18160421</subfield>
            <subfield code="b">1855</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {"date_of_birth": "1816-04-21", "date_of_death": "1855"}


def test_idref_birth_and_death_dates_year_birth():
    """Test date of birth 103 $a pos. 1-8 YYYYMMDD"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="103">
            <subfield code="a">1816?</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {"date_of_birth": "1816?"}


def test_idref_birth_and_death_from_field_200():
    """Test date of birth 200 $f pos. 1-4"""
    xml_part_to_add = """
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">1816-1855</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {"date_of_birth": "1816", "date_of_death": "1855"}

    #  format: "XX.. ?-XX.. ?"
    xml_part_to_add = """
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">18.. ?-19.. ?</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {"date_of_birth": "18..?", "date_of_death": "19..?"}

    #  format: "XXXX-XXXX?"
    xml_part_to_add = """
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">1812-1918?</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {"date_of_birth": "1812", "date_of_death": "1918?"}

    #  format: "XX..-XXXX?"
    xml_part_to_add = """
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">18..-1918?</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {"date_of_birth": "18..", "date_of_death": "1918?"}

    #  format: "XX..-"
    xml_part_to_add = """
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">18..-</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {"date_of_birth": "18.."}

    #  format: "-XXXX?"
    xml_part_to_add = """
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">-1961?</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {"date_of_death": "1961?"}

    #  format: "XXXX"
    xml_part_to_add = """
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">1961</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {"date_of_birth": "1961"}


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
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {"date_of_birth": "1816-04-21", "date_of_death": "1855-03-31"}

    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="103">
            <subfield code="a">1525</subfield>
            <subfield code="b">16010723</subfield>
        </datafield>
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">1525?-1601</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {"date_of_birth": "1525", "date_of_death": "1601-07-23"}

    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="103">
            <subfield code="a">1525</subfield>
            <subfield code="b">16010723</subfield>
        </datafield>
          <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">1525?-1601</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {"date_of_birth": "1525", "date_of_death": "1601-07-23"}


def test_idref_establishment_termination_date():
    """Test date of birth 103 $a YYYY-YYYY with tag 210"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="200">
            <subfield code="f">1816-1855</subfield>
        </datafield>
        <datafield ind1=" " ind2=" " tag="210">
            <subfield code="a">test</subfield>
        </datafield>
    """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_birth_and_death_dates()
    assert trans.json == {
        "date_of_establishment": "1816",
        "date_of_termination": "1855",
    }


def test_idref_birth_and_death_dates_missing():
    """Test date of birth 103 AND 200 missing"""
    xml_part_to_add = ""
    trans = trans_prep("idref", xml_part_to_add)
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
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_biographical_information()
    assert trans.json == {
        "biographical_information": ["Giacomo Nicolini da Sabbio.", "Venezia, Italia"]
    }


def test_idref_biographical_information_missing():
    """Test biographical information 300 $a 34x $a. missing"""
    xml_part_to_add = ""
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_biographical_information()
    assert not trans.json


def test_idref_preferred_name_1():
    """Test Preferred Name for Person 200 $ab"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="200">
            <subfield code="a">Brontë</subfield>
            <subfield code="b">Charlotte</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_preferred_name()
    assert trans.json == {"preferred_name": "Brontë, Charlotte"}


def test_idref_preferred_name_missing():
    """Test Preferred Name for Person 200 $ab missing"""
    xml_part_to_add = ""
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_preferred_name()
    assert not trans.json


def test_idref_preferred_name_missing():
    """Test Preferred Name for Person 100 $a missing"""
    xml_part_to_add = ""
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_preferred_name()
    assert not trans.json


def test_trans_idref_numeration():
    """Test numeration for Person 200 $d"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="200">
            <subfield code="d">II</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_numeration()
    assert trans.json == {"numeration": "II"}


def test_trans_idref_qualifier():
    """Test numeration for Person 200 $c"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="200">
            <subfield code="c">Jr.</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_qualifier()
    assert trans.json == {"qualifier": "Jr."}


def test_idref_variant_name():
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
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_variant_name()
    trans.trans_idref_variant_access_point()
    assert trans.json == {
        "variant_access_point": ["Bell, Currer", "Brontë, Carlotta"],
        "variant_name": ["Bell, Currer", "Brontë, Carlotta"],
    }


def test_idref_variant_name_missing():
    """Test Variant Name for Person 400 $ab missing"""
    xml_part_to_add = ""
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_variant_name()
    trans.trans_idref_variant_access_point()
    assert not trans.json


def test_idref_authorized_access_point():
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
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_authorized_access_point()
    assert trans.json == {
        "authorized_access_point": "Brontë, Charlotte, écrivain, biographe, 1816-1855",
        "type": "bf:Person",
    }


def test_idref_authorized_access_point_missing():
    """Test Authorized access point representing a person 200 $abcdf missing"""
    xml_part_to_add = ""
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_authorized_access_point()
    assert not trans.json


def test_authorized_access_point_diff_order():
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
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_authorized_access_point()
    assert trans.json == {
        "authorized_access_point": "1816-1855, Charlotte, Brontë, écrivain",
        "type": "bf:Person",
    }


def test_authorized_access_point_multiple():
    """Test Authorized access with multiple 200"""
    xml_part_to_add = """
        <datafield tag="200" ind1=" " ind2="1">
            <subfield code="6">a01</subfield>
            <subfield code="7">ba0yfa1y</subfield>
            <subfield code="8">freara</subfield>
            <subfield code="9">0</subfield>
            <subfield code="a">الأشماوي</subfield>
            <subfield code="b">فوزية</subfield>
        </datafield>
        <datafield tag="200" ind1=" " ind2="1">
            <subfield code="6">a01</subfield>
            <subfield code="7">ba0yba0a</subfield>
            <subfield code="8">freara</subfield>
            <subfield code="9">0</subfield>
            <subfield code="a">Ašmāwī</subfield>
            <subfield code="b">Fawziyyaẗ al-</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_authorized_access_point()
    assert trans.json == {
        "authorized_access_point": "Ašmāwī, Fawziyyaẗ al-",
        "type": "bf:Person",
        "variant_access_point": ["الأشماوي, فوزية"],
    }


def test_authorized_access_point_general_order():
    """Test Authorized access point representing a person 200 $abdfc"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="200">
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="8">frefre</subfield>
            <subfield code="a">Brontë</subfield>
            <subfield code="b">Charlotte</subfield>
            <subfield code="f">1816-1855</subfield>
            <subfield code="c">écrivain</subfield>
            <subfield code="e">ignorer le texte</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_authorized_access_point()
    assert trans.json == {
        "authorized_access_point": "Brontë, Charlotte, 1816-1855, écrivain",
        "type": "bf:Person",
    }


def test_idref_parallel_access_point():
    """Test parallel access point 700/710/710."""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="700">
            <subfield code="a">Brontë, Charlotte,</subfield>
            <subfield code="d">1816-1855</subfield>
            <subfield code="c">écrivain</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_parallel_access_point()
    assert trans.json == {
        "parallel_access_point": ["Brontë, Charlotte, 1816-1855, écrivain"]
    }

    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="710">
            <subfield code="a">Paul</subfield>
            <subfield code="b">VI</subfield>
            <subfield code="c">pape</subfield>
            <subfield code="d">1897-1978</subfield>
        </datafield>
     """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_parallel_access_point()
    assert trans.json == {"parallel_access_point": ["Paul. VI (pape) (1897-1978)"]}


def test_idref_country_associated():
    """Test country_associated 102 $a codes ISO 3166-1."""
    xml_part_to_add = """
        <datafield tag="102" ind1=" " ind2=" ">
            <subfield code="a">DE</subfield>
        </datafield>
    """
    trans = trans_prep("idref", xml_part_to_add)
    trans.trans_idref_country_associated()
    assert trans.json == {"country_associated": "gw"}
