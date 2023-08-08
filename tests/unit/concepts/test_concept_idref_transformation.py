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

from concepts_helpers import trans_prep

from rero_mef.marctojson.do_idref_concepts import Transformation


def test_idref_pid():
    """Test pid for 001"""
    xml_part_to_add = """
        <controlfield tag="001">249594463</controlfield>
        <controlfield tag="008">Td6</controlfield>
    """
    trans = trans_prep(Transformation, 'concepts', xml_part_to_add)
    trans.trans_idref_pid()
    assert trans.json == {
        'pid': '249594463'
    }


def test_idref_bnf_type():
    """Test bnf_type for 008"""
    xml_part_to_add = """
        <controlfield tag="008">Td6</controlfield>
    """
    trans = trans_prep(Transformation, 'concepts', xml_part_to_add)
    trans.trans_idref_bnf_type()
    assert trans.json == {
        'bnf_type': 'sujet Rameau'
    }

    xml_part_to_add = """
        <controlfield tag="008">Tf8</controlfield>
    """
    trans = trans_prep(Transformation, 'concepts', xml_part_to_add)
    trans.trans_idref_bnf_type()
    assert trans.json == {
        'bnf_type': 'genre/forme Rameau'
    }


def test_idref_identifier():
    """Test identifier for person 003 033"""
    xml_part_to_add = """
        <controlfield tag="008">Td6</controlfield>
        <controlfield tag="003">
            http://www.idref.fr/249594463</controlfield>
        <datafield tag="033" ind1=" " ind2=" ">
            <subfield code="a">
                http://catalogue.bnf.fr/ark:/12148/cb17876933v</subfield>
            <subfield code="2">BNF</subfield>
            <subfield code="d">20200616</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, 'concepts', xml_part_to_add)
    trans.trans_idref_identifier()
    assert trans.json == {
        'identifiedBy': [
            {
                'type': 'uri',
                'source': 'IDREF',
                'value': 'http://www.idref.fr/249594463'
            },
            {
                'type': 'uri',
                'source': 'BNF',
                'value': 'http://catalogue.bnf.fr/ark:/12148/cb17876933v'
            },
        ]
    }


def test_idref_authorized_access_point():
    """Test authorized_access_point from field 250 280"""
    xml_part_to_add = """
        <controlfield tag="008">Td6</controlfield>
        <datafield tag="250" ind1=" " ind2=" ">
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="9">#</subfield>
            <subfield code="a">Lecture</subfield>
            <subfield code="x">Méthodes d&apos;apprentissage</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, 'concepts', xml_part_to_add)
    trans.trans_idref_authorized_access_point()
    assert trans.json == {
        'authorized_access_point': "Lecture - Méthodes d'apprentissage"
    }

    xml_part_to_add = """
        <controlfield tag="008">Td6</controlfield>
        <datafield tag="280" ind1=" " ind2=" ">
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="9">#</subfield>
            <subfield code="a">Littérature espagnole</subfield>
            <subfield code="z">20e siècle</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, 'concepts', xml_part_to_add)
    trans.trans_idref_authorized_access_point()
    assert trans.json == {
        'authorized_access_point': 'Littérature espagnole - 20e siècle'
    }


def test_idref_variant_access_point():
    """Test variant_access_point from field 450 480"""
    xml_part_to_add = """
        <controlfield tag="008">Td6</controlfield>
        <datafield tag="450" ind1=" " ind2=" ">
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="9">#</subfield>
            <subfield code="a">Jeûne</subfield>
            <subfield code="x">Aspect religieux</subfield>
        </datafield>
        <datafield tag="450" ind1=" " ind2=" ">
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="9">#</subfield>
            <subfield code="a">Jeûne religieux</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, 'concepts', xml_part_to_add)
    trans.trans_idref_variant_access_point()
    assert trans.json == {
        'variant_access_point': [
            'Jeûne - Aspect religieux',
            'Jeûne religieux',
        ]
    }

    xml_part_to_add = """
        <controlfield tag="008">Td6</controlfield>
        <datafield tag="480" ind1=" " ind2=" ">
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="9">#</subfield>
            <subfield code="a">Brevets (droit commercial)</subfield>
        </datafield>
        <datafield tag="480" ind1=" " ind2=" ">
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="9">#</subfield>
            <subfield code="a">Certificats d&apos;addition</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, 'concepts', xml_part_to_add)
    trans.trans_idref_variant_access_point()
    assert trans.json == {
        'variant_access_point': [
            'Brevets (droit commercial)',
            "Certificats d'addition"
        ]
    }


def test_idref_relation():
    """Test trans_idref_relation 550 580"""
    xml_part_to_add = """
        <controlfield tag="008">Td6</controlfield>
        <datafield tag="550" ind1=" " ind2=" ">
            <subfield code="0">Voir aussi</subfield>
            <subfield code="3">095621415</subfield>
            <subfield code="5">z|xxx</subfield>
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="a">Abécédaires espagnols</subfield>
        </datafield>
        <datafield tag="550" ind1=" " ind2=" ">
            <subfield code="0">Voir aussi</subfield>
            <subfield code="3">028465431</subfield>
            <subfield code="5">z|xxx</subfield>
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="a">Abréviations espagnoles</subfield>
        </datafield>
        <datafield tag="550" ind1=" " ind2=" ">
            <subfield code="3">032123477</subfield>
            <subfield code="5">h|xxx</subfield>
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="a">Espagnol (langue)</subfield>
            <subfield code="x">Argot</subfield>
        </datafield>
        <datafield tag="550" ind1=" " ind2=" ">
            <subfield code="3">027861058</subfield>
            <subfield code="5">h|xxx</subfield>
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="a">Espagnol (langue)</subfield>
            <subfield code="x">Dialectes</subfield>
        </datafield>
        <datafield tag="550" ind1=" " ind2=" ">
            <subfield code="3">259276065</subfield>
            <subfield code="5">g|xxx</subfield>
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="a">Langues ibéro-romanes</subfield>
        </datafield>
        <datafield tag="550" ind1=" " ind2=" ">
            <subfield code="3">027471187</subfield>
            <subfield code="5">g|xxx</subfield>
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="a">Langues romanes</subfield>
        </datafield>
        <datafield tag="580" ind1=" " ind2=" ">
            <subfield code="0">Voir aussi</subfield>
            <subfield code="3">034082956</subfield>
            <subfield code="5">z|xxx</subfield>
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="a">Cantiques espagnols</subfield>
        </datafield>
        <datafield tag="580" ind1=" " ind2=" ">
            <subfield code="0">Voir aussi</subfield>
            <subfield code="3">031184030</subfield>
            <subfield code="5">z|xxx</subfield>
            <subfield code="7">ba0yba0y</subfield>
            <subfield code="a">Chansons espagnoles</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, 'concepts', xml_part_to_add)
    trans.trans_idref_relation()
    assert trans.json == {
        'broader': [
            {'authorized_access_point': 'Langues ibéro-romanes'},
            {'authorized_access_point': 'Langues romanes'}
        ],
        'narrower': [
            {'authorized_access_point': 'Espagnol (langue) - Argot'},
            {'authorized_access_point': 'Espagnol (langue) - Dialectes'}
        ],
        'related': [
            {'authorized_access_point': 'Abécédaires espagnols'},
            {'authorized_access_point': 'Abréviations espagnoles'},
            {'authorized_access_point': 'Cantiques espagnols'},
            {'authorized_access_point': 'Chansons espagnoles'}
        ]
    }


def test_idref_classification():
    """Test trans_idref_classification 686."""
    xml_part_to_add = """
        <controlfield tag="008">Td6</controlfield>
        <datafield tag="686" ind1=" " ind2=" ">
            <subfield code="a">370</subfield>
            <subfield code="c">Education et enseignement</subfield>
            <subfield code="2">Note de regroupement par domaine</subfield>
        </datafield>
        <datafield tag="686" ind1=" " ind2=" ">
            <subfield code="a">401</subfield>
            <subfield code="2">Note de regroupement par domaine</subfield>
        </datafield>
    """
    trans = trans_prep(Transformation, 'concepts', xml_part_to_add)
    trans.trans_idref_classification()
    assert trans.json == {
        'classification': [{
            'type': 'bf:ClassificationDdc',
            'classificationPortion': '370',
            'name': "Education et enseignement"
        }, {
            'type': 'bf:ClassificationDdc',
            'classificationPortion': '401',
        }]
    }


def test_idref_close_match():
    """Test trans_idref_classification 822"""
    xml_part_to_add = """
        <controlfield tag="008">Td6</controlfield>
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
    trans = trans_prep(Transformation, 'concepts', xml_part_to_add)
    trans.trans_idref_close_match()
    assert trans.json == {
        'closeMatch': [{
            'authorized_access_point': 'Fasting',
            'source': 'LCSH',
            'identifiedBy': {
                'source': 'LCSH',
                'type': 'uri',
                'value': 'http://id.loc.gov/authorities/subjects/sh85047403'
            }
        }, {
            'authorized_access_point': 'Fasting -- Religious aspects',
            'source': 'LCSH',
            'identifiedBy': {
                'source': 'LCSH',
                'type': 'uri',
                'value': 'http://id.loc.gov/authorities/subjects/sh2003003108'
            }
        }, {
            'authorized_access_point': 'Jeûne',
            'source': 'RVMLaval'
        }, {
            'authorized_access_point': 'Jeûne -- Aspect religieux',
            'source': 'RVMLaval'
        }]
    }


def test_idref_notes():
    """Test """
    xml_part_to_add = """
        <controlfield tag="008">Td6</controlfield>
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
    trans = trans_prep(Transformation, 'concepts', xml_part_to_add)
    trans.trans_idref_note()
    assert trans.json == {
        'note': [{
            'label': [
                'Grand Larousse universel',
                'Les langues du monde / M. Sala, I. Vintila-Radulescu, '
                '1984'
            ],
            'noteType': 'dataSource'
        }, {
            'label': [
                'GDEL: Juin 1940 (appel du 18)'
            ],
            'noteType': 'dataNotFound'
        }, {
            'label': [
                'Processus de perception et de production du langage',
                "S'emploie également en subdivision. Cette subdivision ..."
            ],
            'noteType': 'general'
        }, {
            'label': [
                'Voir aussi la subdivision Métrique et rythmique ...',
                'Voir le descripteur Opposition (science politique).'
            ],
            'noteType': 'seeReference'
        }]
    }


def test_idref_deleted():
    """Test deleted -> leader 6 == d."""
    xml_part_to_add = """
        <leader>     dx  a22     3  45  </leader>
     """
    trans = trans_prep(Transformation, 'concepts', xml_part_to_add)
    trans.trans_idref_deleted()
    assert 'deleted' in trans.json

    xml_part_to_add = """
        <leader>     cx  a22     3  45  </leader>
     """
    trans = trans_prep(Transformation, 'concepts', xml_part_to_add)
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
    trans = trans_prep(Transformation, 'concepts', xml_part_to_add)
    trans.trans_idref_relation_pid()
    assert trans.json == {'relation_pid': {
        'value': '027630501',
        'type': 'redirect_from'
    }}
