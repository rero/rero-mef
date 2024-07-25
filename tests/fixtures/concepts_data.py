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


@pytest.fixture(scope="module")
def concept_rero_data():
    """Concept RERO data."""
    return {
        "$schema": "http://mef.rero.ch/schemas/"
        "concepts_rero/rero-concept-v0.0.1.json",
        "authorized_access_point": "Activités d'éveil",
        "broader": [{"authorized_access_point": "Enseignement primaire"}],
        "identifiedBy": [
            {"source": "RERO", "type": "bf:Local", "value": "A021001006"},
            {"source": "BNF", "type": "bf:Local", "value": "FRBNF11930822X"},
            {"type": "uri", "value": "http://catalogue.bnf.fr/ark:/12148/cb119308220"},
        ],
        "note": [
            {
                "label": ["Vocabulaire de l'éducation / G. Mialaret, 1979"],
                "noteType": "dataSource",
            },
            {"label": ["LCSH, 1995-03"], "noteType": "dataNotFound"},
        ],
        "pid": "A021001006",
        "related": [{"authorized_access_point": "Leçons de choses"}],
        "variant_access_point": [
            "Activités d'éveil (enseignement primaire)",
            "Disciplines d'éveil",
            "Éveil, Activités d'",
        ],
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_idref_data():
    """Concept IdRef data."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_idref/"
        "idref-concept-v0.0.1.json",
        "authorized_access_point": "Franco-provençal (langue) - Dialectes",
        "bnf_type": "sujet Rameau",
        "classification": [
            {
                "classificationPortion": "400",
                "name": "Langues",
                "type": "bf:ClassificationDdc",
            }
        ],
        "deleted": "2022-09-03T07:07:32.526780+00:00",
        "identifiedBy": [
            {"source": "IDREF", "type": "uri", "value": "http://www.idref.fr/050548115"}
        ],
        "narrower": [
            {"authorized_access_point": "Valdôtain (dialecte)"},
            {"authorized_access_point": "Dauphinois (dialecte)"},
            {"authorized_access_point": "Lyonnais (dialecte)"},
            {"authorized_access_point": "Neuchâtelois (dialecte)"},
            {"authorized_access_point": "Savoyard (dialecte)"},
            {"authorized_access_point": "Valaisan (dialecte)"},
            {"authorized_access_point": "Vaudois (dialecte)"},
        ],
        "note": [
            {
                "label": [
                    "Sous cette vedette, éventuellement suivie d'une subdivision "
                    "géographique, on trouve les ouvrages sur les variantes "
                    "dialectales dans les régions franco-provençales "
                    "(Suisse romande, Val d'Aoste, Savoie, Bresse, Lyonnais, "
                    "Forez, Dauphiné), par ex. Franco-provençal (langue) -- "
                    "Dialectes -- France -- Bourg-en-Bresse ; pour les ouvrages "
                    "sur un des dialectes suivants, voir au nom de celui-ci, "
                    "par ex. Savoyard (dialecte)"
                ],
                "noteType": "general",
            }
        ],
        "pid": "050548115",
        "variant_access_point": ["XXXXX", "Dialectes franco-provençaux"],
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_idref_redirect_data():
    """Concept IdRef data with redirect from."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_idref/"
        "idref-concept-v0.0.1.json",
        "authorized_access_point": "Francoprovençal (langue)",
        "bnf_type": "sujet Rameau",
        "broader": [{"authorized_access_point": "Langues romanes"}],
        "classification": [
            {
                "classificationPortion": "400",
                "name": "Langues et linguistique",
                "type": "bf:ClassificationDdc",
            }
        ],
        "closeMatch": [
            {
                "authorized_access_point": "Franco-Provençal dialects",
                "identifiedBy": [
                    {
                        "source": "LCSH",
                        "type": "uri",
                        "value": "http://id.loc.gov/authorities/subjects/sh85051553",
                    }
                ],
                "source": "LCSH",
            },
            {
                "authorized_access_point": "Dialectes franco-provençaux",
                "source": "RVMLaval",
            },
        ],
        "identifiedBy": [
            {
                "source": "IDREF",
                "type": "uri",
                "value": "http://www.idref.fr/027276694",
            },
            {
                "source": "BNF",
                "type": "uri",
                "value": "http://catalogue.bnf.fr/ark:/12148/cb11935379s",
            },
        ],
        "narrower": [
            {"authorized_access_point": "Dauphinois (dialecte)"},
            {"authorized_access_point": "Fribourgeois (dialecte)"},
            {"authorized_access_point": "Lyonnais (dialecte)"},
            {"authorized_access_point": "Neuchâtelois (dialecte)"},
            {"authorized_access_point": "Saugeais (dialecte)"},
            {"authorized_access_point": "Savoyard (dialecte)"},
            {"authorized_access_point": "Valaisan (dialecte)"},
            {"authorized_access_point": "Valdôtain (dialecte)"},
            {"authorized_access_point": "Vaudois (dialecte)"},
        ],
        "note": [
            {
                "label": [
                    "Encycl. universalis (art. : France - Langues régionales) - "
                    "http://www.universalis-edu.com (2009-02-10)",
                    "Grand Larousse universel : franco-provençal",
                    "Les langues du monde / M. Sala, I. Vintila-Radulescu, 1984",
                    "L'aventure des langues en Occident / H. Walter, 1994",
                    "L'aménagement linguistique dans le monde : franco-provençal"
                    " - http://www.tlfq.ulaval.ca (2009-02-10)",
                    "Les langues du monde / A. Meillet, M. Cohen, 1981 : "
                    "franco-provençal",
                    "Ethnologue (15th ed.) : Franco-provençal - "
                    "http://www.ethnologue.com (2009-02-10)",
                ],
                "noteType": "dataSource",
            },
            {
                "label": [
                    "Ensemble de dialectes intermédiaires entre les parlers d'oc "
                    "et les parlers d'oïl, parlés en France, en Italie et en "
                    "Suisse",
                    "Sous cette vedette, on trouve les documents sur l'ensemble "
                    "des dialectes francoprovençaux, ou sur plusieurs dialectes. "
                    "Les documents sur un dialecte particulier se trouvent sous "
                    "les vedettes spécifiques, par ex. : Savoyard (dialecte), ou "
                    "sous la vedette Francoprovençal (langue) suivie d'une "
                    "subdivision géographique, par ex. : Francoprovençal (langue) "
                    "-- France -- Bresse (France)",
                ],
                "noteType": "general",
            },
            {
                "label": ["Voir aussi aux différents dialectes"],
                "noteType": "seeReference",
            },
        ],
        "pid": "027276694",
        "related": [
            {"authorized_access_point": "Bolze (langue)"},
            {"authorized_access_point": "Dictionnaires francoprovençaux"},
            {"authorized_access_point": "Noms géographiques francoprovençaux"},
            {"authorized_access_point": "Chansons francoprovençales"},
            {"authorized_access_point": "Littérature francoprovençale"},
        ],
        "relation_pid": {"type": "redirect_from", "value": "050548115"},
        "variant_access_point": [
            "Arpitan (langue)",
            "Dialectes franco-provençaux",
            "Dialectes francoprovençaux",
            "Français sud-oriental (langue)",
            "Franco-provençal (langue)",
            "Franco-provençal (langue) - Dialectes",
            "Francoprovençal (langue) - Dialectes",
        ],
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_mef_rero_data():
    """Concept MEF data with RERO ref."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_mef/"
        "mef-concept-v0.0.1.json",
        "rero": {"$ref": "https://mef.rero.ch/api/concepts/rero/A021001006"},
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_mef_idref_data():
    """Concept MEF data with IdRef ref."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_mef/"
        "mef-concept-v0.0.1.json",
        "deleted": "2022-09-03T07:07:32.545630+00:00",
        "idref": {"$ref": "https://mef.rero.ch/api/concepts/idref/050548115"},
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_mef_idref_redirect_data():
    """Concept MEF data with IdRef ref and redirect from."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_mef/"
        "mef-concept-v0.0.1.json",
        "idref": {"$ref": "https://mef.rero.ch/api/concepts/idref/027276694"},
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_idref_frbnf_data_close():
    """Concept IdRef data with frbnf."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_idref/idref-concept-v0.0.1.json",
        "authorized_access_point": "Oiseaux nicheurs",
        "bnf_type": "sujet Rameau",
        "broader": [{"authorized_access_point": "Oiseaux - Moeurs et comportement"}],
        "identifiedBy": [
            {
                "source": "IDREF",
                "type": "uri",
                "value": "http://www.idref.fr/032510934",
            },
            {
                "source": "BNF",
                "type": "uri",
                "value": "http://catalogue.bnf.fr/ark:/12148/cb123526871",
            },
            {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF12352687"},
        ],
        "note": [
            {"label": ["GLE"], "noteType": "dataSource"},
            {"label": ["LCSH, 1993-06"], "noteType": "dataNotFound"},
            {
                "label": ["Voir aussi aux noms des différents Oiseaux nicheurs"],
                "noteType": "seeReference",
            },
        ],
        "pid": "032510934",
        "type": "bf:Topic",
        "variant_access_point": ["Nicheurs (oiseaux)"],
    }


@pytest.fixture(scope="module")
def concept_idref_frbnf_data_exact():
    """Concept IdRef data with frbnf."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_idref/idref-concept-v0.0.1.json",
        "authorized_access_point": "Traitement réparti",
        "bnf_type": "sujet Rameau",
        "classification": [
            {"classificationPortion": "621", "type": "bf:ClassificationDdc"}
        ],
        "closeMatch": [
            {
                "authorized_access_point": "Electronic data processing--Distributed processing",
                "identifiedBy": [
                    {
                        "source": "LCSH",
                        "type": "uri",
                        "value": "http://id.loc.gov/authorities/subjects/sh85042293",
                    }
                ],
                "source": "LCSH",
            },
            {"authorized_access_point": "Traitement réparti", "source": "RVMLaval"},
        ],
        "identifiedBy": [
            {
                "source": "IDREF",
                "type": "uri",
                "value": "http://www.idref.fr/027234908",
            },
            {
                "source": "BNF",
                "type": "uri",
                "value": "http://catalogue.bnf.fr/ark:/12148/cb11932111w",
            },
            {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF11932111"},
        ],
        "md5": "15727be7bdf3b2a5c6c23d671b2c8a9f",
        "narrower": [
            {"authorized_access_point": "Apache Storm (plate-forme informatique)"},
            {"authorized_access_point": "Architecture client-serveur (informatique)"},
            {"authorized_access_point": "Informatique omniprésente"},
            {"authorized_access_point": "J2EE (plate-forme informatique)"},
            {"authorized_access_point": "Mémoire partagée répartie"},
            {"authorized_access_point": "NFS (protocole de réseaux d'ordinateurs)"},
            {"authorized_access_point": "NIS (système de gestion de fichiers)"},
            {"authorized_access_point": "PlanetLab (informatique)"},
            {"authorized_access_point": "Répartition de charge (informatique)"},
            {"authorized_access_point": "Réseaux à grande distance (informatique)"},
            {"authorized_access_point": "Réseaux locaux (informatique)"},
            {"authorized_access_point": "Réseaux urbains (informatique)"},
            {"authorized_access_point": "Architecture médiateur-wrapper"},
            {"authorized_access_point": "Systèmes autonomes distribués (informatique)"},
            {"authorized_access_point": "Systèmes d'exploitation répartis"},
            {"authorized_access_point": "Tables de hachage distribuées"},
            {"authorized_access_point": "Bases de données réparties"},
            {"authorized_access_point": "DCOM (architecture des ordinateurs)"},
            {"authorized_access_point": "Enterprise JavaBeans"},
            {"authorized_access_point": "Exclusion mutuelle"},
            {"authorized_access_point": "Grilles informatiques"},
            {"authorized_access_point": "Hadoop (plate-forme informatique)"},
            {"authorized_access_point": "Informatique dans les nuages"},
        ],
        "pid": "027234908",
        "related": [
            {"authorized_access_point": "Apache Spark (langage de programmation)"},
            {"authorized_access_point": "Logique spatiale"},
            {"authorized_access_point": "Observation d'états distribués"},
            {"authorized_access_point": "Ordonnancement (informatique)"},
            {"authorized_access_point": "Réseaux d'ordinateurs"},
            {"authorized_access_point": "Théorie des calculs locaux"},
            {"authorized_access_point": "Traces, Théorie des"},
        ],
        "type": "bf:Topic",
        "variant_access_point": [
            "Applications distribuées (informatique)",
            "Applications réparties (informatique)",
            "Systèmes répartis (informatique)",
            "Informatique - Traitement réparti",
            "Informatique distribuée",
            "Informatique répartie",
            "Multi-agents, Systèmes",
            "Systèmes distribués (informatique)",
            "Systèmes informatiques distribués",
            "Systèmes informatiques répartis",
            "Systèmes multi-agents",
        ],
    }


@pytest.fixture(scope="module")
def concept_gnd_frbnf_data_close():
    """Concept GND data with frbnf."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_gnd/gnd-concept-v0.0.1.json",
        "authorized_access_point": "Brutvögel",
        "identifiedBy": [
            {"source": "GND", "type": "uri", "value": "http://d-nb.info/gnd/4146776-0"},
            {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)041467760"},
            {"source": "GND", "type": "bf:Nbn", "value": "(DE-588)4146776-0"},
        ],
        "closeMatch": [
            {
                "authorized_access_point": "Oiseaux nicheurs",
                "source": "GND",
                "identifiedBy": [
                    {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)1134790635"},
                    {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF12352687"},
                    {
                        "type": "uri",
                        "value": "https://data.bnf.fr/ark:/12148/cb123526871",
                    },
                ],
            }
        ],
        "pid": "041467760",
        "type": "bf:Topic",
        "broader": [{"authorized_access_point": "Vögel"}],
        "variant_access_point": ["Brutvogel", "Einheimische Vögel"],
    }


@pytest.fixture(scope="module")
def concept_gnd_frbnf_data_exact():
    """Concept GND data with frbnf."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_gnd/gnd-concept-v0.0.1.json",
        "authorized_access_point": "Dezentrale Datenverarbeitung",
        "broader": [{"authorized_access_point": "Datenverarbeitung"}],
        "closeMatch": [
            {
                "authorized_access_point": "Elaborazione distribuita",
                "identifiedBy": [
                    {
                        "source": "GND",
                        "type": "bf:Nbn",
                        "value": "(DE-101)1254324852",
                    },
                    {
                        "source": "IT",
                        "type": "bf:Nbn",
                        "value": "3277",
                    },
                    {
                        "type": "uri",
                        "value": "http://purl.org/bncf/tid/3277",
                    },
                ],
                "source": "GND",
            },
            {
                "authorized_access_point": "Proceso distribuido (Informática)",
                "identifiedBy": [
                    {
                        "source": "GND",
                        "type": "bf:Nbn",
                        "value": "(DE-101)1254419977",
                    },
                    {
                        "source": "SPMABN",
                        "type": "bf:Nbn",
                        "value": "XX545920",
                    },
                    {
                        "type": "uri",
                        "value": "https://datos.bne.es/resource/XX545920",
                    },
                ],
                "source": "GND",
            },
        ],
        "exactMatch": [
            {
                "authorized_access_point": "Electronic data processing",
                "identifiedBy": [
                    {
                        "source": "GND",
                        "type": "bf:Nbn",
                        "value": "(DE-101)1133615708",
                    },
                    {
                        "source": "DLC",
                        "type": "bf:Nbn",
                        "value": "sh85042293",
                    },
                    {
                        "type": "uri",
                        "value": "http://id.loc.gov/authorities/subjects/sh85042293",
                    },
                ],
                "source": "GND",
            },
            {
                "authorized_access_point": "Traitement réparti",
                "identifiedBy": [
                    {
                        "source": "GND",
                        "type": "bf:Nbn",
                        "value": "(DE-101)1133615708",
                    },
                    {
                        "source": "BNF",
                        "type": "bf:Nbn",
                        "value": "FRBNF11932111",
                    },
                    {
                        "type": "uri",
                        "value": "https://data.bnf.fr/ark:/12148/cb11932111w",
                    },
                ],
                "source": "GND",
            },
        ],
        "identifiedBy": [
            {
                "source": "GND",
                "type": "uri",
                "value": "http://d-nb.info/gnd/7545389-7",
            },
            {
                "source": "GND",
                "type": "bf:Nbn",
                "value": "(DE-101)981473830",
            },
            {
                "source": "GND",
                "type": "bf:Nbn",
                "value": "(DE-588)7545389-7",
            },
        ],
        "md5": "628a19be80ecd77321435a7122f8539b",
        "note": [
            {
                "label": [
                    "Form der elektronischen Datenverarbeitung, bei der mehrere Rechner zwar über Rechnernetz "
                    "verbunden sind, Daten austauschen und gemeinsame Ressourcen nutzen können, jedoch jeweils "
                    "autonom eigene Aufgaben erledigen. (B Computer)",
                    "Für das Arbeiten mehrerer vernetzter Rechner an Teilaufgaben desselben Problems verwende "
                    "Verteiltes System.",
                ],
                "noteType": "general",
            }
        ],
        "pid": "981473830",
        "type": "bf:Topic",
        "variant_access_point": [
            "Decentralized Data Processing",
            "Distributed Data Processing System (Dezentralisation)",
            "DDPS",
            "Verteilte Datenverarbeitung (Dezentralisation)",
            "Verteiltes Datenverarbeitungssystem (Dezentralisation)",
        ],
    }
