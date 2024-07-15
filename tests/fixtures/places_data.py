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

"""Places data."""

import pytest


@pytest.fixture(scope="module")
def place_idref_data():
    """Place IdRef data."""
    return {
        "$schema": "https://mef.rero.ch/schemas/places_idref/"
        "idref-place-v0.0.1.json",
        "authorized_access_point": "Port-Valais (Suisse)",
        "bnf_type": "sujet Rameau",
        "classification": [
            {"classificationPortion": "914", "type": "bf:ClassificationDdc"}
        ],
        "identifiedBy": [
            {
                "source": "IDREF",
                "type": "uri",
                "value": "http://www.idref.fr/271330163",
            },
            {
                "source": "BNF",
                "type": "uri",
                "value": "http://catalogue.bnf.fr/ark:/12148/cb16965305j",
            },
        ],
        "note": [
            {
                "label": [
                    "Port-Valais - http://www.port-valais.ch (2015-05-18)",
                    "Dict. historique de la Suisse - "
                    "http://www.hls-dhs-dss.ch (2015-05-18)",
                ],
                "noteType": "dataSource",
            },
            {
                "label": [
                    "Commune du canton du Valais, district de Monthey, "
                    "comprenant les villages du Bouveret et des Evouettes"
                ],
                "noteType": "general",
            },
        ],
        "pid": "271330163",
        "type": "bf:Place",
        "deleted": "2022-09-03T07:07:32.526780+00:00",
    }


@pytest.fixture(scope="module")
def place_idref_redirect_data():
    """Place IdRef data with redirect from."""
    return {
        "$schema": "https://mef.rero.ch/schemas/places_idref/"
        "idref-place-v0.0.1.json",
        "authorized_access_point": "Port-Valais (Suisse)",
        "bnf_type": "sujet Rameau",
        "classification": [
            {"classificationPortion": "914", "type": "bf:ClassificationDdc"}
        ],
        "identifiedBy": [
            {
                "source": "IDREF",
                "type": "uri",
                "value": "http://www.idref.fr/271330163",
            },
            {
                "source": "BNF",
                "type": "uri",
                "value": "http://catalogue.bnf.fr/ark:/12148/cb16965305j",
            },
        ],
        "note": [
            {
                "label": [
                    "Port-Valais - http://www.port-valais.ch (2015-05-18)",
                    "Dict. historique de la Suisse - "
                    "http://www.hls-dhs-dss.ch (2015-05-18)",
                ],
                "noteType": "dataSource",
            },
            {
                "label": [
                    "Commune du canton du Valais, district de Monthey, "
                    "comprenant les villages du Bouveret et des Evouettes"
                ],
                "noteType": "general",
            },
        ],
        "pid": "271330163x2",
        "type": "bf:Place",
        "relation_pid": {"type": "redirect_from", "value": "271330163"},
    }


@pytest.fixture(scope="module")
def place_mef_idref_data():
    """Place MEF data with IdRef ref."""
    return {
        "$schema": "https://mef.rero.ch/schemas/places_mef/" "mef-place-v0.0.1.json",
        "deleted": "2022-09-03T07:07:32.545630+00:00",
        "idref": {"$ref": "https://mef.rero.ch/api/places/idref/271330163"},
        "type": "bf:Place",
    }


@pytest.fixture(scope="module")
def place_mef_idref_redirect_data():
    """Place MEF data with IdRef ref and redirect from."""
    return {
        "$schema": "https://mef.rero.ch/schemas/places_mef/" "mef-place-v0.0.1.json",
        "idref": {"$ref": "https://mef.rero.ch/api/places/idref/271330163x2"},
        "type": "bf:Place",
    }


@pytest.fixture(scope="module")
def place_gnd_data():
    """Place IdRef data."""
    return {
        "authorized_access_point": "Nordschleswig",
        "closeMatch": [
            {
                "authorized_access_point": "Nordschleswig",
                "source": "GND",
                "identifiedBy": {
                    "type": "bf:Nbn",
                    "value": "(DE-101)992404371",
                    "source": "(DE-101)992404371",
                },
            }
        ],
        "identifiedBy": [
            {"source": "GND", "type": "uri", "value": "http://d-nb.info/gnd/4075476-5"},
            {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)040754766"},
            {"source": "GND", "type": "bf:Nbn", "value": "(DE-588)4075476-5"},
        ],
        "pid": "040754766",
        "type": "bf:Place",
        "broader": [
            {"authorized_access_point": "Herzogtum Schleswig"},
            {"authorized_access_point": "Da\u0308nemark"},
        ],
        "variant_access_point": [
            "Su\u0308dliches Ju\u0308tland",
            "Ju\u0308tland",
            "Schleswig",
            "Su\u0308dju\u0308tland",
            "Nordslesvig",
            "Da\u0308nemark",
            "Su\u0308dda\u0308nemark",
            "S\u00f8nderjylland",
        ],
        "md5": "4928526430cc69ce78284fc42389d088",
    }


@pytest.fixture(scope="module")
def place_gnd_redirect_data():
    """Place IdRef data with redirect from."""
    return {
        "authorized_access_point": "Arhiepiscopia Romanului şi Bacăului",
        "deleted": "2024-07-17T15:06:23.887218+00:00",
        "identifiedBy": [
            {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)1332367461"},
            {"source": "GND", "type": "bf:Nbn", "value": "(DE-588)1332367461"},
        ],
        "pid": "1332367461",
        "type": "bf:Place",
        "relation_pid": {"value": "1332364101", "type": "redirect_to"},
        "md5": "4f6181dd5cb82589e6d17b5c3dd33372",
    }
