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

from places_helpers import trans_prep

from rero_mef.marctojson.do_gnd_places import Transformation


def test_gnd_pid():
    """Test pid for 001"""
    xml_part_to_add = """
        <controlfield tag="001">993772048</controlfield>
    """
    trans = trans_prep(Transformation, "places", xml_part_to_add)
    trans.trans_gnd_pid()
    assert trans.json == {"pid": "993772048", "type": "bf:Place"}


def test_gnd_identifier():
    """Test identifier for person 024, 035"""
    xml_part_to_add = """
        <datafield tag="024" ind1=" " ind2=" ">
            <subfield code="a">7655914-2</subfield>
            <subfield code="0">http://d-nb.info/gnd/7655914-2</subfield>
            <subfield code="2">gnd</subfield>
        </datafield>
        <datafield tag="035" ind1=" " ind2=" ">
            <subfield code="a">(DE-101)993772048d</subfield>
        </datafield>
        <datafield tag="035" ind1=" " ind2=" ">
            <subfield code="a">(DE-588)7655914-2</subfield>
        </datafield>
        <datafield tag="035" ind1=" " ind2=" ">
            <subfield code="a">(DE-588c)7655914-2</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, "places", xml_part_to_add)
    trans.trans_gnd_identifier()
    assert trans.json == {
        "identifiedBy": [
            {
                "type": "uri",
                "source": "GND",
                "value": "http://d-nb.info/gnd/7655914-2",
            },
            {
                "type": "bf:Nbn",
                "source": "GND",
                "value": "(DE-101)993772048d",
            },
            {
                "type": "bf:Nbn",
                "source": "GND",
                "value": "(DE-588)7655914-2",
            },
        ],
    }


def test_gnd_authorized_access_point():
    """Test authorized_access_point from field 151"""
    xml_part_to_add = """
    <datafield tag="151" ind1=" " ind2=" ">
        <subfield code="a">Maria Königin</subfield>
        <subfield code="g">Grünwald, München</subfield>
    </datafield>
    """
    trans = trans_prep(Transformation, "places", xml_part_to_add)
    trans.trans_gnd_authorized_access_point()
    assert trans.json == {
        "authorized_access_point": "Maria Königin (Grünwald, München)"
    }


def test_gnd_variant_access_point():
    """Test variant_access_point from field 451"""
    xml_part_to_add = """
        <datafield tag="451" ind1=" " ind2=" ">
            <subfield code="a">Tiefenbach-Kiesling</subfield>
        </datafield>
        <datafield tag="451" ind1=" " ind2=" ">
            <subfield code="a">Kießling</subfield>
            <subfield code="g">Tiefenbach, Passau</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, "places", xml_part_to_add)
    trans.trans_gnd_variant_access_point()
    assert trans.json == {
        "variant_access_point": ["Tiefenbach-Kiesling", "Kießling (Tiefenbach, Passau)"]
    }


def test_gnd_relation():
    """Test trans_gnd_relation 551"""
    xml_part_to_add = """
        <datafield tag="551" ind1=" " ind2=" ">
            <subfield code="0">(DE-101)041079302</subfield>
            <subfield code="0">(DE-588)4107930-9</subfield>
            <subfield code="0">https://d-nb.info/gnd/4107930-9</subfield>
            <subfield code="a">Weißes Meer</subfield>
            <subfield code="4">obpa</subfield>
            <subfield code="4">https://d-nb.info/standards/elementset/gnd#broaderTermPartitive</subfield>
            <subfield code="w">r</subfield>
            <subfield code="i">Oberbegriff partitiv</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, "places", xml_part_to_add)
    trans.trans_gnd_relation()
    assert trans.json == {
        "broader": [
            {"authorized_access_point": "Weißes Meer"},
        ]
    }


def test_gnd_classification():
    """Test trans_gnd_classification ???."""
    # TODO: trans_gnd_classification


def test_gnd_close_match():
    """Test trans_gnd_classification 751"""
    xml_part_to_add = """
        <datafield tag="751" ind1=" " ind2=" ">
            <subfield code="0">(DE-101)997977663</subfield>
            <subfield code="0">(ZBW)091419204</subfield>
            <subfield code="a">Venedig</subfield>
            <subfield code="4">EQ</subfield>
            <subfield code="4">https://d-nb.info/standards/elementset/gnd#exactEquivalence</subfield>
            <subfield code="i">exakte Aequivalenz</subfield>
            <subfield code="2">stw</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, "places", xml_part_to_add)
    trans.trans_gnd_match()
    assert trans.json == {
        "exactMatch": [
            {
                "authorized_access_point": "Venedig",
                "source": "GND",
                "identifiedBy": [
                    {
                        "source": "GND",
                        "type": "bf:Nbn",
                        "value": "(DE-101)997977663",
                    },
                    {
                        "source": "ZBW",
                        "type": "bf:Nbn",
                        "value": "091419204",
                    },
                ],
            }
        ]
    }


def test_gnd_notes():
    """Test trans_gnd_note 678 670"""
    xml_part_to_add = """
        <datafield tag="670" ind1=" " ind2=" ">
            <subfield code="a">Vorlage; Internet</subfield>
            <subfield code="u">http://www.historisches-unterfranken.uni-wuerzburg.de/db_swu_wuestung.php</subfield>
        </datafield>
        <datafield tag="678" ind1=" " ind2=" ">
            <subfield code="b">Bach bei Theilheim, Würzburg</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, "places", xml_part_to_add)
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
    trans = trans_prep(Transformation, "places", xml_part_to_add)
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
    trans = trans_prep(Transformation, "places", xml_part_to_add)
    trans.trans_gnd_relation()
    assert trans.json == {
        "relation_pid": {"value": "004459091", "type": "redirect_to"},
    }
