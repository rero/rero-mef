# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2024 RERO
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

"""Test GND auth person."""

import os

from agents_helpers import build_xml_record_file, trans_prep
from pymarc import marcxml

from rero_mef.marctojson.do_gnd_agent import Transformation


def test_no_person_or_organisation():
    """Test no person or organisation."""
    xml_part_to_add = """
        <datafield tag="075" ind1=" " ind2=" ">
            <subfield code="b">s</subfield>
            <subfield code="2">gndgen</subfield>
        </datafield>
    """
    build_xml_record_file(xml_part_to_add)
    current_dir = os.path.dirname(__file__)
    file_name = os.path.join(current_dir, "examples/xml_minimal_record.xml")
    records = marcxml.parse_xml_to_array(file_name, strict=False, normalize_form=None)
    data = Transformation(marc=records[0], logger=None, verbose=False, transform=True)
    assert data.json_dict == {
        "NO TRANSFORMATION": "Not a person or organisation: bf:Topic"
    }


def test_no_100_110_111():
    """Test np 100, 110, 111."""
    xml_part_to_add = """
        <datafield tag="075" ind1=" " ind2=" ">
            <subfield code="b">p</subfield>
            <subfield code="2">gndgen</subfield>
        </datafield>
        <datafield tag="075" ind1=" " ind2=" ">
            <subfield code="b">piz</subfield>
            <subfield code="2">gndspec</subfield>
        </datafield>
    """
    build_xml_record_file(xml_part_to_add)
    current_dir = os.path.dirname(__file__)
    file_name = os.path.join(current_dir, "examples/xml_minimal_record.xml")
    records = marcxml.parse_xml_to_array(file_name, strict=False, normalize_form=None)
    data = Transformation(marc=records[0], logger=None, verbose=False, transform=True)
    assert data.json_dict == {"NO TRANSFORMATION": "No 100 or 110 or 111"}


def test_gnd_deleted():
    """Test deleted -> leader 6 == d."""
    xml_part_to_add = """
        <leader>00000nz  a2200000oc 4500</leader>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_deleted()
    assert not trans.json

    xml_part_to_add = """
        <leader>00000cz  a2200000oc 4500</leader>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_deleted()
    assert "deleted" in trans.json

    xml_part_to_add = """
        <leader>00000xz  a2200000oc 4500</leader>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_deleted()
    assert "deleted" in trans.json

    xml_part_to_add = """
        <leader>00000dz  a2200000oc 4500</leader>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_deleted()
    assert "deleted" in trans.json


def test_gnd_relation_pid():
    """Test new pid 682 $0 $i == 'Umlenkung'.

    nid = 132911-X -> pid = 100937187
    """
    xml_part_to_add = """
        <datafield tag="682" ind1=" " ind2=" ">
            <subfield code="i">Umlenkung</subfield>
            <subfield code="0">(DE-101)100937187</subfield>
            <subfield code="0">(DE-588)132911-X</subfield>
            <subfield code="0">https://d-nb.info/gnd/100937187</subfield>
            <subfield code="a">Albericus, Londoniensis</subfield>
        </datafield>
    """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_relation_pid()
    assert trans.json == {"relation_pid": {"value": "100937187", "type": "redirect_to"}}


def test_gnd_gender_female():
    """Test gender 375 $a 1 = male, 2 = female, " " = not known."""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="375">
            <subfield code="a">2</subfield>
        </datafield>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_gender()
    assert trans.json == {"gender": "female"}


def test_gnd_gender_male():
    """Test gender 375 $a 1 = male, 2 = female, " " = not known."""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="375">
            <subfield code="a">1</subfield>
        </datafield>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_gender()
    assert trans.json == {"gender": "male"}


def test_gnd_gender_unknown():
    """Test gender 375 $a 1 = male, 2 = female, " " = not known."""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="375">
            <subfield code="a"> </subfield>
        </datafield>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_gender()
    assert trans.json == {"gender": "not known"}


def test_gnd_gender_missing():
    """Test gender 375 missing"""
    xml_part_to_add = ""
    trans = trans_prep("gnd", xml_part_to_add)
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
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_language()
    assert trans.json == {"language": ["fre", "eng"]}


def test_gnd_language_missing():
    """Test language of person 377 missing"""
    xml_part_to_add = ""
    trans = trans_prep("gnd", xml_part_to_add)
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
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_identifier()
    assert trans.json == {
        "identifier": "http://d-nb.info/gnd/100000193",
        "identifiedBy": [
            {"source": "GND", "type": "uri", "value": "http://d-nb.info/gnd/100000193"}
        ],
    }


def test_gnd_identifier_missing():
    """Test identifier for person 001 missing"""
    xml_part_to_add = ""
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_identifier()
    assert not trans.json


def test_gnd_pid():
    """Test pid for person"""
    xml_part_to_add = """
        <controlfield tag="001">118577166</controlfield>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_pid()
    assert trans.json == {
        "pid": "118577166",
    }


def test_gnd_establishment_termination_date():
    """Test date of birth 100 $d YYYY-YYYY"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="d">1816-1855</subfield>
        </datafield>
        <datafield ind1=" " ind2=" " tag="110">
            <subfield code="a">test</subfield>
        </datafield>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_birth_and_death_dates()
    assert trans.json == {
        "date_of_establishment": "1816",
        "date_of_termination": "1855",
    }


def test_gnd_birth_and_death_dates_year_birth_death():
    """Test date of birth 100 $d YYYY-YYYY"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="d">1816-1855</subfield>
        </datafield>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_birth_and_death_dates()
    assert trans.json == {"date_of_birth": "1816", "date_of_death": "1855"}


def test_gnd_birth_and_death_dates_year_birth():
    """Test date of birth 100 $d YYYY-"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="d">1816-</subfield>
        </datafield>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_birth_and_death_dates()
    assert trans.json == {"date_of_birth": "1816"}


def test_gnd_birth_and_death_dates_year_death():
    """Test date of birth 100 $d -YYYY"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="d">-1855</subfield>
        </datafield>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_birth_and_death_dates()
    assert trans.json == {"date_of_death": "1855"}


def test_gnd_birth_and_death_dates_year_date():
    """Test date of birth 100 $d YYYYMMDD"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="d">18551201</subfield>
        </datafield>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_birth_and_death_dates()
    assert trans.json == {"date_of_birth": "1855-12-01"}


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
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_birth_and_death_dates()
    assert trans.json == {"date_of_birth": "06.06.1875", "date_of_death": "12.08.1955"}


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
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_birth_and_death_dates()
    assert trans.json == {"date_of_birth": "1582", "date_of_death": "26.11.1631"}


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
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_birth_and_death_dates()
    assert trans.json == {"date_of_birth": "06.06.1875"}


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
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_birth_and_death_dates()
    assert trans.json == {"date_of_death": "12.08.1955"}


def test_gnd_birth_and_death_dates_missing():
    """Test date of birth 100 AND 548 missing"""
    xml_part_to_add = ""
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_birth_and_death_dates()
    assert not trans.json


def test_gnd_conference():
    """Test conference false: 075 $b = b true: 075 $b = f"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="075">
            <subfield code="b">b</subfield>
        </datafield>
        <datafield ind1=" " ind2=" " tag="111">
            <subfield code="a">test</subfield>
        </datafield>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_conference()
    assert trans.json == {"conference": False}
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="075">
            <subfield code="b">f</subfield>
        </datafield>
        <datafield ind1=" " ind2=" " tag="111">
            <subfield code="a">test</subfield>
        </datafield>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_conference()
    assert trans.json == {"conference": True}
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="075">
            <subfield code="b">x</subfield>
        </datafield>
        <datafield ind1=" " ind2=" " tag="111">
            <subfield code="a">test</subfield>
        </datafield>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_conference()
    assert trans.json is None


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
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_biographical_information()
    assert trans.json == {
        "biographical_information": [
            "Dizionario Biografico (1960), Camillo, treccani.it/enc",
            "Dt. Franziskaner-Minorit",
        ]
    }


def test_gnd_biographical_information_missing():
    """Test biographical information 678 missing"""
    xml_part_to_add = ""
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_biographical_information()
    assert not trans.json


def test_gnd_preferred_name():
    """Test Preferred Name for Person 100 $a"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="a">Bauer, Johann Gottfried</subfield>
        </datafield>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_preferred_name()
    assert trans.json == {"preferred_name": "Bauer, Johann Gottfried"}


def test_gnd_preferred_name_organisation():
    """Test Preferred Name for Organisation 110 $a"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="110">
            <subfield code="a">SBeurret Bailly Auktionen</subfield>
        </datafield>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_preferred_name()
    assert trans.json == {"preferred_name": "SBeurret Bailly Auktionen"}


def test_gnd_preferred_name_missing():
    """Test Preferred Name for Person 100 $a missing"""
    xml_part_to_add = ""
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_preferred_name()
    assert not trans.json


def test_gnd_numeration():
    """Test numeration for Person 100 $b"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="b">II</subfield>
        </datafield>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_numeration()
    assert trans.json == {"numeration": "II"}


def test_gnd_qualifier():
    """Test numeration for Person 100 $c"""
    xml_part_to_add = """
        <datafield ind1=" " ind2=" " tag="100">
            <subfield code="c">Jr.</subfield>
        </datafield>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_qualifier()
    assert trans.json == {"qualifier": "Jr."}


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
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_variant_name()
    trans.trans_gnd_variant_access_point()
    assert trans.json == {
        "variant_access_point": ["Barbanson, Konstantin von", "Barbançon, Konstantyn"],
        "variant_name": ["Barbanson, Konstantin von", "Barbanc\u0327on, Konstantyn"],
    }


def test_gnd_variant_name_organisation():
    """Test Variant Name for Person 410 $a"""
    xml_part_to_add = """
        <datafield tag="410" ind1="2" ind2=" ">
            <subfield code="a">The Young Gods</subfield>
            <subfield code="g">Musikgruppe</subfield>
        </datafield>
        <datafield tag="410" ind1="2" ind2=" ">
            <subfield code="a">TYG</subfield>
        </datafield>
            """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_variant_name()
    trans.trans_gnd_variant_access_point()
    assert trans.json == {
        "variant_access_point": ["The Young Gods. Musikgruppe", "TYG"],
        "variant_name": ["The Young Gods", "TYG"],
    }


def test_gnd_variant_name_missing():
    """Test Variant Name for Person 400 $a missing"""
    xml_part_to_add = ""
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_variant_name()
    trans.trans_gnd_variant_access_point()
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
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_authorized_access_point()
    assert trans.json == {
        "authorized_access_point": "Johannes Paul, II., Papst, 1920-2005",
        "type": "bf:Person",
    }


def test_gnd_authorized_access_point_organisation():
    """Test Authorized access point representing a person 100 $abcd"""
    xml_part_to_add = """
        <datafield tag="110" ind1="2" ind2=" ">
            <subfield code="a">The Young Gods</subfield>
            <subfield code="g">Musikgruppe</subfield>
        </datafield>
     """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_authorized_access_point()
    assert trans.json == {
        "authorized_access_point": "The Young Gods. Musikgruppe",
        "type": "bf:Organisation",
    }


def test_gnd_authorized_access_point_missing():
    """Test Authorized access point representing a person 100 $abcd missing"""
    xml_part_to_add = ""
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_authorized_access_point()
    assert not trans.json


def test_gnd_parallel_access_point():
    """Test Authorized access point representing a person 100 $abcd"""
    xml_part_to_add = """
        <datafield tag="700" ind1="1" ind2="7">
            <subfield code="a">Goethe, Johann Wolfgang von</subfield>
            <subfield code="d">1749-1832</subfield>
        </datafield>
    """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_parallel_access_point()
    assert trans.json == {
        "parallel_access_point": ["Goethe, Johann Wolfgang von, 1749-1832"]
    }


def test_gnd_parallel_access_point_organisation():
    """Test Authorized access point representing a person 100 $abcd"""
    xml_part_to_add = """
        <datafield tag="710" ind1="1" ind2="7">
            <subfield code="a">Гёте, Йоҳанн Волфганг</subfield>
            <subfield code="d">1749-1832</subfield>
        </datafield>
    """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_parallel_access_point()
    assert trans.json == {"parallel_access_point": ["Гёте, Йоҳанн Волфганг, 1749-1832"]}


def test_gnd_country_associated():
    """Test country_associated 043 $c codes ISO 3166-1."""
    xml_part_to_add = """
        <datafield tag="043" ind1=" " ind2=" ">
            <subfield code="c">XA-DE</subfield>
        </datafield>
    """
    trans = trans_prep("gnd", xml_part_to_add)
    trans.trans_gnd_country_associated()
    assert trans.json == {"country_associated": "gw"}
