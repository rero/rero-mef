# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2022 RERO
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

"""Concepts data."""

import pytest


@pytest.fixture(scope='module')
def concept_rero_data():
    """Concept RERO record."""
    return {
        "$schema":
            "https://mef.rero.ch/schemas/"
            "concepts_rero/rero-concept-v0.0.1.json",
        "authorized_access_point": "Activités d'éveil",
        "broader": [{
            "authorized_access_point": "Enseignement primaire"
        }],
        "identifiedBy": [{
            "source": "RERO",
            "type": "bf:Local",
            "value": "A021001006"
        }, {
            "source": "BNF",
            "type": "bf:Local",
            "value": "FRBNF11930822X"
        }, {
            "type": "uri",
            "value": "http://catalogue.bnf.fr/ark:/12148/cb119308220"
        }],
        "note": [{
            "label": [
                "Vocabulaire de l'éducation / G. Mialaret, 1979"
            ],
            "noteType": "dataSource"
        }, {
            "label": ["LCSH, 1995-03"],
            "noteType": "dataNotFound"
        }],
        "pid": "A021001006",
        "related": [{
            "authorized_access_point": "Leçons de choses"
        }],
        "variant_access_point": [
            "Activités d'éveil (enseignement primaire)",
            "Disciplines d'éveil",
            "Éveil, Activités d'"
        ]
    }
