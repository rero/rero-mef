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
