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

"""Test RERO auth contribution."""

from places_helpers import trans_prep

from rero_mef.marctojson.do_idref_places import Transformation


def test_idref_pid():
    """Test pid for 001"""
    xml_part_to_add = """
        <controlfield tag="001">027227812</controlfield>
        <controlfield tag="008">Tg5</controlfield>
    """
    trans = trans_prep(Transformation, "places", xml_part_to_add)
    trans.trans_idref_pid()
    assert trans.json == {"pid": "027227812", "type": "bf:Place"}


def test_idref_identifier():
    """Test identifier for person 003 033"""
    xml_part_to_add = """
        <controlfield tag="008">Tg5</controlfield>
        <controlfield tag="003">http://www.idref.fr/027227812</controlfield>
        <datafield tag="033" ind1=" " ind2=" ">
            <subfield code="a">
                http://catalogue.bnf.fr/ark:/12148/cb11931552b
            </subfield>
            <subfield code="2">BNF</subfield>
            <subfield code="d">20180619</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, "places", xml_part_to_add)
    trans.trans_idref_identifier()
    assert trans.json == {
        "identifiedBy": [
            {
                "type": "uri",
                "source": "IDREF",
                "value": "http://www.idref.fr/027227812",
            },
            {
                "type": "uri",
                "source": "BNF",
                "value": "http://catalogue.bnf.fr/ark:/12148/cb11931552b",
            },
        ]
    }


def test_idref_authorized_access_point():
    """Test authorized_access_point from field 215"""
    xml_part_to_add = """
    <datafield tag="215" ind1=" " ind2=" ">
        <subfield code="7">ba0yba0y</subfield>
        <subfield code="9">1</subfield>
        <subfield code="a">Gdańsk (Pologne)</subfield>
    </datafield>
    """
    trans = trans_prep(Transformation, "places", xml_part_to_add)
    trans.trans_idref_authorized_access_point()
    assert trans.json == {"authorized_access_point": "Gdańsk (Pologne)"}


def test_idref_variant_access_point():
    """Test variant_access_point from field 415"""
    xml_part_to_add = """
        <controlfield tag="008">Tg5</controlfield>
        <datafield tag="415" ind1=" " ind2=" ">
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="9">1</subfield>
            <subfield code="a">Dantzig (Pologne)</subfield>
        </datafield>
        <datafield tag="415" ind1=" " ind2=" ">
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="a">Gedania</subfield>
        </datafield>
        <datafield tag="415" ind1=" " ind2=" ">
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="a">Gedani</subfield>
        </datafield>
        <datafield tag="415" ind1=" " ind2=" ">
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="9">1</subfield>
            <subfield code="a">Danzig (Pologne)</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, "places", xml_part_to_add)
    trans.trans_idref_variant_access_point()
    assert trans.json == {
        "variant_access_point": [
            "Dantzig (Pologne)",
            "Gedania",
            "Gedani",
            "Danzig (Pologne)",
        ]
    }


def test_idref_relation():
    """Test trans_idref_relation 515"""
    xml_part_to_add = """
        <controlfield tag="008">Tg5</controlfield>
        <datafield tag="515" ind1=" " ind2=" ">
            <subfield code="Q">15285409</subfield>
            <subfield code="5">g|xxx</subfield>
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="a">Pologne</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, "places", xml_part_to_add)
    trans.trans_idref_relation()
    assert trans.json == {
        "broader": [
            {"authorized_access_point": "Pologne"},
        ]
    }


def test_idref_classification():
    """Test trans_idref_classification 686."""
    xml_part_to_add = """
        <controlfield tag="008">Tg5</controlfield>
        <datafield tag="686" ind1=" " ind2=" ">
            <subfield code="a">370</subfield>
            <subfield code="c">Education et enseignement</subfield>
            <subfield code="2">Note de regroupement par domaine</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, "places", xml_part_to_add)
    trans.trans_idref_classification()
    assert trans.json == {
        "classification": [
            {
                "type": "bf:ClassificationDdc",
                "classificationPortion": "370",
                "name": "Education et enseignement",
            }
        ]
    }


def test_idref_close_match():
    """Test trans_idref_classification 822"""
    xml_part_to_add = """
        <controlfield tag="008">Tg5</controlfield>
        <datafield tag="822" ind1=" " ind2=" ">
            <subfield code="a">Fasting</subfield>
            <subfield code="2">LCSH</subfield>
            <subfield code="u">
            http://id.loc.gov/authorities/subjects/sh85047403</subfield>
            <subfield code="d">2022-07-22</subfield>
        </datafield>
        <datafield tag="822" ind1=" " ind2=" ">
            <subfield code="a">Fasting -- Religious aspects</subfield>
            <subfield code="2">LCSH</subfield>
            <subfield code="u">
            http://id.loc.gov/authorities/subjects/sh2003003108</subfield>
            <subfield code="d">2022-07-22</subfield>
        </datafield>
        <datafield tag="822" ind1=" " ind2=" ">
            <subfield code="a">Jeûne</subfield>
            <subfield code="2">RVMLaval</subfield>
            <subfield code="d">2022-07-22</subfield>
        </datafield>
        <datafield tag="822" ind1=" " ind2=" ">
            <subfield code="a">Jeûne -- Aspect religieux</subfield>
            <subfield code="2">RVMLaval</subfield>
            <subfield code="d">2022-07-22</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, "places", xml_part_to_add)
    trans.trans_idref_close_match()
    assert trans.json == {
        "closeMatch": [
            {
                "authorized_access_point": "Fasting",
                "source": "LCSH",
                "identifiedBy": {
                    "source": "LCSH",
                    "type": "uri",
                    "value": "http://id.loc.gov/authorities/subjects/sh85047403",
                },
            },
            {
                "authorized_access_point": "Fasting -- Religious aspects",
                "source": "LCSH",
                "identifiedBy": {
                    "source": "LCSH",
                    "type": "uri",
                    "value": "http://id.loc.gov/authorities/subjects/sh2003003108",
                },
            },
            {"authorized_access_point": "Jeûne", "source": "RVMLaval"},
            {
                "authorized_access_point": "Jeûne -- Aspect religieux",
                "source": "RVMLaval",
            },
        ]
    }


def test_idref_notes():
    """Test"""
    xml_part_to_add = """
        <controlfield tag="008">Tg5</controlfield>
        <datafield tag="810" ind1=" " ind2=" ">
            <subfield code="a">Grand Larousse universel</subfield>
        </datafield>
        <datafield tag="810" ind1=" " ind2=" ">
            <subfield code="a">
                Les langues du monde / M. Sala, I. Vintila-Radulescu, 1984
            </subfield>
        </datafield>
        <datafield tag="815" ind1=" " ind2=" ">
            <subfield code="a">GDEL: Juin 1940 (appel du 18)</subfield>
        </datafield>
        <datafield tag="300" ind1=" " ind2=" ">
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="a">
                Processus de perception et de production du langage
            </subfield>
        </datafield>
        <datafield tag="330" ind1="1" ind2=" ">
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="a">
                S&apos;emploie également en subdivision. Cette subdivision ...
            </subfield>
        </datafield>
        <datafield tag="305" ind1="1" ind2=" ">
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="a">
                Voir aussi la subdivision Métrique et rythmique ...
            </subfield>
        </datafield>
        <datafield tag="320" ind1="1" ind2=" ">
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="a">
                Voir le descripteur Opposition (science politique).
            </subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, "places", xml_part_to_add)
    trans.trans_idref_note()
    assert trans.json == {
        "note": [
            {
                "label": [
                    "Grand Larousse universel",
                    "Les langues du monde / M. Sala, I. Vintila-Radulescu, " "1984",
                ],
                "noteType": "dataSource",
            },
            {"label": ["GDEL: Juin 1940 (appel du 18)"], "noteType": "dataNotFound"},
            {
                "label": [
                    "Processus de perception et de production du langage",
                    "S'emploie également en subdivision. Cette subdivision ...",
                ],
                "noteType": "general",
            },
            {
                "label": [
                    "Voir aussi la subdivision Métrique et rythmique ...",
                    "Voir le descripteur Opposition (science politique).",
                ],
                "noteType": "seeReference",
            },
        ]
    }


def test_idref_deleted():
    """Test deleted -> leader 6 == d."""
    xml_part_to_add = """
        <leader>     dx  a22     3  45  </leader>
     """
    trans = trans_prep(Transformation, "places", xml_part_to_add)
    trans.trans_idref_deleted()
    assert "deleted" in trans.json

    xml_part_to_add = """
        <leader>     cx  a22     3  45  </leader>
     """
    trans = trans_prep(Transformation, "places", xml_part_to_add)
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
    """
    trans = trans_prep(Transformation, "places", xml_part_to_add)
    trans.trans_idref_relation_pid()
    assert trans.json == {
        "identifiedBy": [
            {"source": "VIAF", "type": "uri", "value": "http://viaf.org/viaf/124265140"}
        ],
        "relation_pid": {"value": "027630501", "type": "redirect_from"},
    }
