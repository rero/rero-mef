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

"""Test RERO auth contribution."""

from concepts_helpers import trans_prep

from rero_mef.marctojson.do_gnd_concepts import Transformation


def test_gnd_pid():
    """Test pid for 001"""
    xml_part_to_add = """
        <controlfield tag="001">976573474</controlfield>
    """
    trans = trans_prep(Transformation, "concepts", xml_part_to_add)
    trans.trans_gnd_pid()
    assert trans.json == {"pid": "976573474", "type": "bf:Topic"}


def test_gnd_identifier():
    """Test identifier for person 024, 035"""
    xml_part_to_add = """
        <datafield tag="024" ind1=" " ind2=" ">
            <subfield code="a">4844250-1</subfield>
            <subfield code="0">http://d-nb.info/gnd/4844250-1</subfield>
            <subfield code="2">gnd</subfield>
        </datafield>
        <datafield tag="035" ind1=" " ind2=" ">
            <subfield code="a">(DE-101)976573474</subfield>
        </datafield>
        <datafield tag="035" ind1=" " ind2=" ">
            <subfield code="a">(DE-588)4844250-1</subfield>
        </datafield>
        <datafield tag="035" ind1=" " ind2=" ">
            <subfield code="a">(DE-588c)4844250</subfield>
            <subfield code="9">v:zg</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, "concepts", xml_part_to_add)
    trans.trans_gnd_identifier()
    assert trans.json == {
        "identifiedBy": [
            {
                "type": "uri",
                "source": "GND",
                "value": "http://d-nb.info/gnd/4844250-1",
            },
            {
                "type": "bf:Nbn",
                "source": "GND",
                "value": "(DE-101)976573474",
            },
            {
                "type": "bf:Nbn",
                "source": "GND",
                "value": "(DE-588)4844250-1",
            },
        ],
    }


def test_gnd_authorized_access_point():
    """Test authorized_access_point from field 150"""
    xml_part_to_add = """
    <datafield tag="150" ind1=" " ind2=" ">
        <subfield code="a">Magnet</subfield>
        <subfield code="g">Druckschrift, Offenbach, Main</subfield>
    </datafield>
    """
    trans = trans_prep(Transformation, "concepts", xml_part_to_add)
    trans.trans_gnd_authorized_access_point()
    assert trans.json == {
        "authorized_access_point": "Magnet (Druckschrift, Offenbach, Main)"
    }


def test_gnd_variant_access_point():
    """Test variant_access_point from field 450"""
    xml_part_to_add = """
        <datafield tag="450" ind1=" " ind2=" ">
            <subfield code="a">Ohio</subfield>
            <subfield code="g">Druckschrift</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, "concepts", xml_part_to_add)
    trans.trans_gnd_variant_access_point()
    assert trans.json == {"variant_access_point": ["Ohio (Druckschrift)"]}


def test_gnd_relation():
    """Test trans_gnd_relation 550"""
    xml_part_to_add = """
        <datafield tag="550" ind1=" " ind2=" ">
            <subfield code="0">(DE-101)041994493</subfield>
            <subfield code="0">(DE-588)4199449-8</subfield>
            <subfield code="0">https://d-nb.info/gnd/4199449-8</subfield>
            <subfield code="a">Antiqua</subfield>
            <subfield code="4">obal</subfield>
            <subfield code="4">https://d-nb.info/standards/elementset/gnd#broaderTermGeneral</subfield>
            <subfield code="w">r</subfield>
            <subfield code="i">Oberbegriff allgemein</subfield>
        </datafield>
        <datafield tag="550" ind1=" " ind2=" ">
            <subfield code="0">(DE-101)992744342</subfield>
            <subfield code="0">(DE-588)7647113-5</subfield>
            <subfield code="0">https://d-nb.info/gnd/7647113-5</subfield>
            <subfield code="a">Ohio-Kursiv</subfield>
            <subfield code="4">vbal</subfield>
            <subfield code="4">https://d-nb.info/standards/elementset/gnd#relatedTerm</subfield>
            <subfield code="w">r</subfield>
            <subfield code="i">Verwandter Begriff</subfield>
        </datafield>    """
    trans = trans_prep(Transformation, "concepts", xml_part_to_add)
    trans.trans_gnd_relation()
    assert trans.json == {
        "broader": [
            {"authorized_access_point": "Antiqua"},
        ],
        "related": [
            {"authorized_access_point": "Ohio-Kursiv"},
        ],
    }


def test_gnd_classification():
    """Test trans_gnd_classification ???."""
    # TODO: trans_gnd_classification


def test_gnd_close_match():
    """Test trans_gnd_classification 750"""
    xml_part_to_add = """
        <datafield tag="750" ind1=" " ind2=" ">
            <subfield code="0">(DE-101)1134384173</subfield>
            <subfield code="0">(DLC)sh85009231</subfield>
            <subfield code="0">http://id.loc.gov/authorities/subjects/sh85009231</subfield>
            <subfield code="a">Atlases</subfield>
            <subfield code="4">EQ</subfield>
            <subfield code="4">https://d-nb.info/standards/elementset/gnd#equivalence</subfield>
            <subfield code="i">Aequivalenz</subfield>
            <subfield code="2">lcsh</subfield>
            <subfield code="9">L:eng</subfield>
        </datafield>
        <datafield tag="750" ind1=" " ind2=" ">
            <subfield code="0">(DE-101)125348144X</subfield>
            <subfield code="0">(DNLM)D020466</subfield>
            <subfield code="0">http://id.nlm.nih.gov/mesh/D020466</subfield>
            <subfield code="a">Atlas</subfield>
            <subfield code="4">EQ</subfield>
            <subfield code="4">https://d-nb.info/standards/elementset/gnd#exactEquivalence</subfield>
            <subfield code="i">exakte Aequivalenz</subfield>
            <subfield code="2">mesh</subfield>
            <subfield code="9">L:eng</subfield>
            <subfield code="9">v:Ausg. 2022|2023</subfield>
        </datafield>    """
    trans = trans_prep(Transformation, "concepts", xml_part_to_add)
    trans.trans_gnd_match()
    assert trans.json == {
        "closeMatch": [
            {
                "authorized_access_point": "Atlases",
                "source": "DLC",
                "identifiedBy": [
                    {
                        "source": "DLC",
                        "type": "uri",
                        "value": "http://id.loc.gov/authorities/subjects/sh85009231",
                    },
                    {
                        "source": "DLC",
                        "type": "bf:Nbn",
                        "value": "sh85009231",
                    },
                    {
                        "source": "GND",
                        "type": "bf:Nbn",
                        "value": "(DE-101)1134384173",
                    },
                ],
            }
        ],
        "exactMatch": [
            {
                "authorized_access_point": "Atlas",
                "source": "DNLM",
                "identifiedBy": [
                    {
                        "source": "DNLM",
                        "type": "uri",
                        "value": "http://id.nlm.nih.gov/mesh/D020466",
                    },
                    {"source": "DNLM", "type": "bf:Nbn", "value": "D020466"},
                    {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)125348144X"},
                ],
            },
        ],
    }


def test_gnd_notes():
    """Test trans_gnd_note 670 677 678 680"""
    xml_part_to_add = """
        <datafield tag="670" ind1=" " ind2=" ">
            <subfield code="a">Vorlage; Internet</subfield>
            <subfield code="u">http://www.historisches-unterfranken.uni-wuerzburg.de/db_swu_wuestung.php</subfield>
        </datafield>
        <datafield tag="678" ind1=" " ind2=" ">
            <subfield code="b">Bach bei Theilheim, Würzburg</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, "concepts", xml_part_to_add)
    trans.trans_gnd_note()
    assert trans.json == {
        "note": [
            {
                "label": [
                    "Vorlage; Internet - http://www.historisches-unterfranken.uni-wuerzburg.de/db_swu_wuestung.php"
                ],
                "noteType": "dataSource",
            },
            {
                "label": ["Bach bei Theilheim, Würzburg"],
                "noteType": "general",
            },
        ]
    }


def test_gnd_deleted():
    """Test deleted -> leader 6 == d."""
    xml_part_to_add = """
        <leader>     dx  a22     3  45  </leader>
     """
    trans = trans_prep(Transformation, "concepts", xml_part_to_add)
    trans.trans_gnd_deleted()
    assert "deleted" in trans.json


def test_gnd_relation_pid():
    """Test relation pid."""
    xml_part_to_add = """
        <datafield tag="682" ind1=" " ind2=" ">
            <subfield code="i">Umlenkung</subfield>
            <subfield code="0">(DE-101)004459091</subfield>
            <subfield code="0">(DE-588)1098274-7</subfield>
            <subfield code="0">https://d-nb.info/gnd/1098274-7</subfield>
            <subfield code="a">Isarkreis</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, "concepts", xml_part_to_add)
    trans.trans_gnd_relation_pid()
    assert trans.json == {
        "relation_pid": {"value": "004459091", "type": "redirect_to"},
    }
