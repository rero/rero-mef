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

"""Test RERO auth contribution."""

from concepts_helpers import trans_prep


def test_rero_identifier():
    """Test identifier for person 035 016 679"""
    xml_part_to_add = """
        <datafield tag="035" ind1=" " ind2=" ">
            <subfield code="a">A021029523</subfield>
        </datafield>
        <datafield tag="016" ind1=" " ind2=" ">
            <subfield code="a">FRBNF120611480</subfield>
        </datafield>
        <datafield tag="679" ind1=" " ind2=" ">
            <subfield code="u">
                http://catalogue.bnf.fr/ark:/12148/cb120611486
            </subfield>
        </datafield>
    """

    trans = trans_prep('concepts', xml_part_to_add)
    trans.trans_rero_identifier()
    assert trans.json == {
        'pid': 'A021029523',
        'identifiedBy': [
            {
                'type': 'bf:Local',
                'source': 'RERO',
                'value': 'A021029523'
            },
            {
                'type': 'bf:Local',
                'source': 'BNF',
                'value': 'FRBNF120611480'
            },
            {
                'type': 'uri',
                'value': 'http://catalogue.bnf.fr/ark:/12148/cb120611486'
            }
        ]
    }


def test_rero_bnf_type():
    """Test bnf type"""
    xml_part_to_add = """
        <datafield tag="075" ind1=" " ind2=" ">
            <subfield code="a">Genre / Fiction</subfield>
        </datafield>
    """

    trans = trans_prep('concepts', xml_part_to_add)
    trans.trans_rero_bnf_type()
    assert trans.json == {
        'bnf_type': 'Genre / Fiction'
    }


def test_rero_authorized_access_point():
    """Test authorized_access_point from field 150 155"""
    xml_part_to_add = """
        <datafield tag="150" ind1=" " ind2=" ">
            <subfield code="a">
                Bibliothèques publiques - Services audiovisuels
            </subfield>
        </datafield>
    """
    trans = trans_prep('concepts', xml_part_to_add)
    trans.trans_rero_authorized_access_point()
    assert trans.json == {
        'authorized_access_point':
            'Bibliothèques publiques - Services audiovisuels'
    }

    xml_part_to_add = """
        <datafield tag="155" ind1=" " ind2=" ">
            <subfield code="a">
                [Bandes dessinées fantastiques]
            </subfield>
        </datafield>
    """
    trans = trans_prep('concepts', xml_part_to_add)
    trans.trans_rero_authorized_access_point()
    assert trans.json == {
        'authorized_access_point': '[Bandes dessinées fantastiques]'
    }


def test_rero_variant_access_point():
    """Test variant_access_point from field 450 455"""
    xml_part_to_add = """
        <datafield tag="450" ind1=" " ind2=" ">
            <subfield code="a">
                Bibliothèques publiques et audiovisuel
            </subfield>
        </datafield>
        <datafield tag="450" ind1=" " ind2=" ">
            <subfield code="a">
                Bibliothèques publiques et audiovisuel 2
            </subfield>
        </datafield>
    """
    trans = trans_prep('concepts', xml_part_to_add)
    trans.trans_rero_variant_access_point()
    assert trans.json == {
        'variant_access_point': [
            'Bibliothèques publiques et audiovisuel',
            'Bibliothèques publiques et audiovisuel 2'
        ]
    }

    xml_part_to_add = """
        <datafield tag="455" ind1=" " ind2=" ">
            <subfield code="a">[Fantastique]</subfield>
            <subfield code="x">Bandes dessinées</subfield>
        </datafield>
    """
    trans = trans_prep('concepts', xml_part_to_add)
    trans.trans_rero_variant_access_point()
    assert trans.json == {
        'variant_access_point': [
            '[Fantastique] - Bandes dessinées'
        ]
    }


def test_rero_relation():
    """Test trans_rero_relation 550 555"""
    xml_part_to_add = """
        <datafield tag="550" ind1=" " ind2=" ">
            <subfield code="a">Bibliothèques - Services audiovisuels</subfield>
            <subfield code="w">g</subfield>
        </datafield>
        <datafield tag="550" ind1=" " ind2=" ">
            <subfield code="a">Ordinateurs neuronaux</subfield>
            <subfield code="w">h</subfield>
        </datafield>

    """
    trans = trans_prep('concepts', xml_part_to_add)
    trans.trans_rero_relation()
    assert trans.json == {
        'broader': [{
            'authorized_access_point': 'Bibliothèques - Services audiovisuels',
        }],
        'narrower': [{
            'authorized_access_point': 'Ordinateurs neuronaux',
        }],
    }

    xml_part_to_add = """
        <datafield tag="555" ind1=" " ind2=" ">
            <subfield code="a">Livres en carton</subfield>
        </datafield>
        <datafield tag="555" ind1=" " ind2=" ">
            <subfield code="a">Livres en plastique</subfield>
        </datafield>
    """
    trans = trans_prep('concepts', xml_part_to_add)
    trans.trans_rero_relation()
    assert trans.json == {
        'related': [
            {
                'authorized_access_point': 'Livres en carton',
            },
            {
                'authorized_access_point': 'Livres en plastique',
            }
        ],
    }


def test_rero_classification():
    """Test """
    xml_part_to_add = """
        <datafield tag="072" ind1=" " ind2=" ">
          <subfield code="a">020 - Sciences de l'information</subfield>
        </datafield>
    """
    trans = trans_prep('concepts', xml_part_to_add)
    trans.trans_rero_classification()
    assert trans.json == {
        'classification': [{
            'type': 'bf:ClassificationDdc',
            'classificationPortion': '020',
            'name': "Sciences de l'information"
        }]
    }


def test_rero_close_match():
    """Test """
    xml_part_to_add = """
        <datafield tag="682" ind1=" " ind2=" ">
          <subfield code="a">Public Libraries</subfield>
          <subfield code="v">LCSH</subfield>
        </datafield>
    """
    trans = trans_prep('concepts', xml_part_to_add)
    trans.trans_rero_close_match()
    assert trans.json == {
        'closeMatch': {
            'authorized_access_point': 'Public Libraries',
            'source': 'LCSH'
        }
    }


def test_rero_notes():
    """Test """
    xml_part_to_add = """
        <datafield tag="670" ind1=" " ind2=" ">
            <subfield code="a">
                Grand Larousse universel (art. : Livre)
            </subfield>
        </datafield>
        <datafield tag="675" ind1=" " ind2=" ">
            <subfield code="a">Laval RVM (en ligne), 2004-11-23</subfield>
        </datafield>
        <datafield tag="680" ind1=" " ind2=" ">
            <subfield code="a">
                Mers profondément engagées dans la masse des ...
            </subfield>
        </datafield>
        <datafield tag="667" ind1=" " ind2=" ">
            <subfield code="a">Note interne</subfield>
        </datafield>
        <datafield tag="260" ind1=" " ind2="9">
            <subfield code="a">
                Voir le descripteur Opposition (science politique) ...
            </subfield>
        </datafield>
        <datafield tag="260" ind1=" " ind2="9">
            <subfield code="a">
                Combiner un des descripteurs Mouvements ...
            </subfield>
        </datafield>
        <datafield tag="260" ind1=" " ind2=" ">
            <subfield code="a">
                Voir les vedettes : Mouvements contestataires ; ...
                </subfield>
        </datafield>
        <datafield tag="260" ind1=" " ind2=" ">
            <subfield code="a">
                Voir les vedettes du type : Antifascisme ; ...
            </subfield>
        </datafield>
        <datafield tag="260" ind1=" " ind2=" ">
            <subfield code="a">
                Voir aux mouvements d'opposition particuliers, par ...
            </subfield>
        </datafield>
        <datafield tag="360" ind1=" " ind2=" ">
            <subfield code="a">
                Voir aussi aux mers et océans particuliers
            </subfield>
        </datafield>
        <datafield tag="016" ind1=" " ind2=" ">
            <subfield code="9">VF3, NC3, NC30</subfield>
        </datafield>
    """
    trans = trans_prep('concepts', xml_part_to_add)
    trans.trans_rero_note()
    assert trans.json == {
        'note': [
            {
              'label': ['Grand Larousse universel (art. : Livre)'],
              'noteType': 'dataSource'
            },
            {
              'label': ['Laval RVM (en ligne), 2004-11-23'],
              'noteType': 'dataNotFound'
            },
            {
                'label': [
                    'Mers profondément engagées dans la masse des ...'
                ],
                'noteType': 'general'
            },
            {
                'label': ['Note interne'],
                'noteType': 'nonPublic'},
            {
                'label': [
                    'Voir le descripteur Opposition (science politique) ...',
                    'Combiner un des descripteurs Mouvements ...',
                    'Voir les vedettes : Mouvements contestataires ; ...',
                    'Voir les vedettes du type : Antifascisme ; ...',
                    "Voir aux mouvements d'opposition particuliers, par ..."
                ],
                'noteType': 'seeReference'
            },
            {
                'label': ['Voir aussi aux mers et océans particuliers'],
                'noteType': 'seeAlsoReference'
            },
            {
                'label': ['VF3, NC3, NC30'],
                'noteType': 'REROtreatment'
            }
        ]
    }
