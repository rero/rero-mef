# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Concepts data."""

import pytest


@pytest.fixture(scope="module")
def concept_rero_data():
    """Concept RERO data."""
    return {
        "$schema": "http://mef.rero.ch/schemas/concepts_rero/rero-concept-v0.0.1.json",
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
        "$schema": "https://mef.rero.ch/schemas/concepts_idref/idref-concept-v0.0.1.json",
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
        "identifiedBy": [{"source": "IDREF", "type": "uri", "value": "http://www.idref.fr/050548115"}],
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
                    (
                        "Sous cette vedette, éventuellement suivie d'une subdivision "
                        "géographique, on trouve les ouvrages sur les variantes "
                        "dialectales dans les régions franco-provençales "
                        "(Suisse romande, Val d'Aoste, Savoie, Bresse, Lyonnais, "
                        "Forez, Dauphiné), par ex. Franco-provençal (langue) -- "
                        "Dialectes -- France -- Bourg-en-Bresse ; pour les ouvrages "
                        "sur un des dialectes suivants, voir au nom de celui-ci, "
                        "par ex. Savoyard (dialecte)"
                    )
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
        "$schema": "https://mef.rero.ch/schemas/concepts_idref/idref-concept-v0.0.1.json",
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
                    (
                        "Encycl. universalis (art. : France - Langues régionales) - "
                        "http://www.universalis-edu.com (2009-02-10)"
                    ),
                    "Grand Larousse universel : franco-provençal",
                    "Les langues du monde / M. Sala, I. Vintila-Radulescu, 1984",
                    "L'aventure des langues en Occident / H. Walter, 1994",
                    (
                        "L'aménagement linguistique dans le monde : franco-provençal"
                        " - http://www.tlfq.ulaval.ca (2009-02-10)"
                    ),
                    "Les langues du monde / A. Meillet, M. Cohen, 1981 : franco-provençal",
                    "Ethnologue (15th ed.) : Franco-provençal - http://www.ethnologue.com (2009-02-10)",
                ],
                "noteType": "dataSource",
            },
            {
                "label": [
                    (
                        "Ensemble de dialectes intermédiaires entre les parlers d'oc "
                        "et les parlers d'oïl, parlés en France, en Italie et en "
                        "Suisse"
                    ),
                    (
                        "Sous cette vedette, on trouve les documents sur l'ensemble "
                        "des dialectes francoprovençaux, ou sur plusieurs dialectes. "
                        "Les documents sur un dialecte particulier se trouvent sous "
                        "les vedettes spécifiques, par ex. : Savoyard (dialecte), ou "
                        "sous la vedette Francoprovençal (langue) suivie d'une "
                        "subdivision géographique, par ex. : Francoprovençal (langue) "
                        "-- France -- Bresse (France)"
                    ),
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
        "$schema": "https://mef.rero.ch/schemas/concepts_mef/mef-concept-v0.0.1.json",
        "rero": {"$ref": "https://mef.rero.ch/api/concepts/rero/A021001006"},
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_mef_idref_data():
    """Concept MEF data with IdRef ref."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_mef/mef-concept-v0.0.1.json",
        "deleted": "2022-09-03T07:07:32.545630+00:00",
        "idref": {"$ref": "https://mef.rero.ch/api/concepts/idref/050548115"},
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_mef_idref_redirect_data():
    """Concept MEF data with IdRef ref and redirect from."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_mef/mef-concept-v0.0.1.json",
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
        "classification": [{"classificationPortion": "621", "type": "bf:ClassificationDdc"}],
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
def concept_idref_027269698_data():
    """Concept IdRef data for the live FRBNF linking case."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_idref/idref-concept-v0.0.1.json",
        "authorized_access_point": "Arbres",
        "identifiedBy": [
            {"source": "IDREF", "type": "uri", "value": "http://www.idref.fr/027269698"},
            {"source": "BNF", "type": "uri", "value": "http://catalogue.bnf.fr/ark:/12148/cb11934786x"},
            {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF11934786"},
        ],
        "pid": "027269698",
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_gnd_040048454_data():
    """Concept GND data for the live FRBNF linking case."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_gnd/gnd-concept-v0.0.1.json",
        "authorized_access_point": "Baum",
        "closeMatch": [
            {
                "authorized_access_point": "Arbres",
                "identifiedBy": [
                    {"source": "BNF", "type": "uri", "value": "https://data.bnf.fr/ark:/12148/cb11934786x"},
                    {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF11934786"},
                    {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)1133622844"},
                ],
                "source": "BNF",
            }
        ],
        "pid": "040048454",
        "type": "bf:Topic",
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
                    (
                        "Form der elektronischen Datenverarbeitung, bei der mehrere Rechner zwar über Rechnernetz "
                        "verbunden sind, Daten austauschen und gemeinsame Ressourcen nutzen können, jedoch jeweils "
                        "autonom eigene Aufgaben erledigen. (B Computer)"
                    ),
                    (
                        "Für das Arbeiten mehrerer vernetzter Rechner an Teilaufgaben desselben Problems verwende "
                        "Verteiltes System."
                    ),
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


@pytest.fixture(scope="module")
def concept_idref_link_data():
    """Concept IdRef `Discours argumentatif`, FRBNF12468269 in identifiedBy."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_idref/idref-concept-v0.0.1.json",
        "authorized_access_point": "Discours argumentatif",
        "bnf_type": "sujet Rameau",
        "identifiedBy": [
            {"source": "IDREF", "type": "uri", "value": "http://www.idref.fr/033869235"},
            {"source": "BNF", "type": "uri", "value": "http://catalogue.bnf.fr/ark:/12148/cb12468269t"},
            {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF12468269"},
        ],
        "pid": "033869235",
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_gnd_link_data():
    """Concept GND `Verkettung`, FRBNF12468269 in closeMatch."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_gnd/gnd-concept-v0.0.1.json",
        "authorized_access_point": "Verkettung",
        "closeMatch": [
            {
                "authorized_access_point": "Discours argumentatif",
                "identifiedBy": [
                    {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)1134566506"},
                    {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF12468269"},
                    {"type": "uri", "value": "https://data.bnf.fr/ark:/12148/cb12468269t"},
                ],
                "source": "GND",
            }
        ],
        "identifiedBy": [
            {"source": "GND", "type": "uri", "value": "http://d-nb.info/gnd/4187851-6"},
            {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)041878515"},
        ],
        "pid": "041878515",
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_rero_link_data():
    """Concept RERO `Agriculture biologique`, FRBNF119308529 in identifiedBy.

    The only RERO/GND overlap in `data/corero.json`: the same BNF number as
    `concept_gnd_rero_link_data`, but written as `bf:Local` with the check
    character kept (14 chars instead of 13).
    """
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_rero/rero-concept-v0.0.1.json",
        "authorized_access_point": "Agriculture biologique",
        "identifiedBy": [
            {"source": "RERO", "type": "bf:Local", "value": "A021001021"},
            {"source": "BNF", "type": "bf:Local", "value": "FRBNF119308529"},
            {"type": "uri", "value": "http://catalogue.bnf.fr/ark:/12148/cb11930852x"},
        ],
        "pid": "A021001021",
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_gnd_rero_link_data():
    """Concept GND `Biologisch-dynamische Wirtschaftsweise`, FRBNF11930852."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_gnd/gnd-concept-v0.0.1.json",
        "authorized_access_point": "Biologisch-dynamische Wirtschaftsweise",
        "closeMatch": [
            {
                "authorized_access_point": "Organic farming",
                "identifiedBy": [
                    {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)1134597304"},
                    {"source": "DLC", "type": "bf:Nbn", "value": "sh85095504"},
                ],
                "source": "GND",
            },
            {
                "authorized_access_point": "Agriculture biologique",
                "identifiedBy": [
                    {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)1134597304"},
                    {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF11930852"},
                    {"type": "uri", "value": "https://data.bnf.fr/ark:/12148/cb11930852x"},
                ],
                "source": "GND",
            },
        ],
        "identifiedBy": [
            {"source": "GND", "type": "uri", "value": "http://d-nb.info/gnd/4006856-0"},
            {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)040068560"},
        ],
        "pid": "040068560",
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_gnd_kochbuch_data():
    """Concept GND `Kochbuch`, one BNF number in two duplicated closeMatch entries.

    Live record https://mef.rero.ch/api/concepts/gnd/041142403. The duplicated
    entries used to count as two matches and disqualified the record.
    """
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_gnd/gnd-concept-v0.0.1.json",
        "authorized_access_point": "Kochbuch",
        "closeMatch": [
            {
                "authorized_access_point": "Food writing",
                "identifiedBy": [
                    {"source": "DLC", "type": "bf:Nbn", "value": "sh96003769"},
                    {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)1133792855"},
                ],
                "source": "DLC",
            },
            {
                "authorized_access_point": "Livres de cuisine",
                "identifiedBy": [
                    {"source": "BNF", "type": "uri", "value": "https://data.bnf.fr/ark:/12148/cb12425736p"},
                    {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF12425736"},
                    {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)1133792855"},
                ],
                "source": "BNF",
            },
            {
                "authorized_access_point": "Livres de cuisine",
                "identifiedBy": [
                    {"source": "BNF", "type": "uri", "value": "https://data.bnf.fr/ark:/12148/cb12425736p"},
                    {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF12425736"},
                    {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)1134838743"},
                ],
                "source": "BNF",
            },
            {
                "authorized_access_point": "Libros de cocina",
                "identifiedBy": [{"source": "SPMABN", "type": "bf:Nbn", "value": "XX556809"}],
                "source": "SPMABN",
            },
        ],
        "identifiedBy": [{"source": "GND", "type": "bf:Nbn", "value": "(DE-101)041142403"}],
        "pid": "041142403",
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_idref_livres_cuisine_data():
    """Concept IdRef `Livres de cuisine`, FRBNF12425736.

    Live record https://mef.rero.ch/api/concepts/idref/033386390.
    """
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_idref/idref-concept-v0.0.1.json",
        "authorized_access_point": "Livres de cuisine",
        "closeMatch": [{"authorized_access_point": "Livres de cuisine", "source": "RVMLaval"}],
        "identifiedBy": [
            {"source": "IDREF", "type": "uri", "value": "http://www.idref.fr/033386390"},
            {"source": "BNF", "type": "uri", "value": "http://catalogue.bnf.fr/ark:/12148/cb12425736p"},
            {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF12425736"},
        ],
        "pid": "033386390",
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_gnd_baum_data():
    """Concept GND `Baum`, BNF number in closeMatch only.

    Live record https://mef.rero.ch/api/concepts/gnd/040048454. Its
    `exactMatch` entries carry no BNF number at all, so the BNF number of the
    `closeMatch` entry `Arbres` is the association identifier.
    """
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_gnd/gnd-concept-v0.0.1.json",
        "authorized_access_point": "Baum",
        "exactMatch": [
            {
                "authorized_access_point": "trees",
                "identifiedBy": [
                    {"source": "ITRFAO", "type": "bf:Nbn", "value": "7887"},
                    {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)1256195146"},
                ],
                "source": "ITRFAO",
            },
            {
                "authorized_access_point": "Baum",
                "identifiedBy": [{"source": "ZBW", "type": "bf:Nbn", "value": "14101-3"}],
                "source": "ZBW",
            },
        ],
        "closeMatch": [
            {
                "authorized_access_point": "Trees",
                "identifiedBy": [{"source": "DLC", "type": "bf:Nbn", "value": "sh85137241"}],
                "source": "DLC",
            },
            {
                "authorized_access_point": "Arbres",
                "identifiedBy": [
                    {"source": "BNF", "type": "uri", "value": "https://data.bnf.fr/ark:/12148/cb11934786x"},
                    {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF11934786"},
                    {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)1133622844"},
                ],
                "source": "BNF",
            },
            {
                "authorized_access_point": "Alberi",
                "identifiedBy": [{"source": "IT", "type": "bf:Nbn", "value": "11392"}],
                "source": "IT",
            },
        ],
        "identifiedBy": [{"source": "GND", "type": "bf:Nbn", "value": "(DE-101)040048454"}],
        "pid": "040048454",
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_gnd_sieg_data():
    """Concept GND `Sieg`, a closeMatch whose BNF number and ark disagree.

    Live record https://mef.rero.ch/api/concepts/gnd/04291373X. The number
    points at IdRef `Épée (sport)`, the ark at IdRef `Victoire`.
    """
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_gnd/gnd-concept-v0.0.1.json",
        "authorized_access_point": "Sieg",
        "closeMatch": [
            {
                "authorized_access_point": "Victoire",
                "identifiedBy": [
                    {"source": "BNF", "type": "uri", "value": "https://data.bnf.fr/ark:/12148/cb151000210"},
                    {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF12308292"},
                    {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)1334552770"},
                ],
                "source": "BNF",
            }
        ],
        "identifiedBy": [{"source": "GND", "type": "bf:Nbn", "value": "(DE-101)04291373X"}],
        "pid": "04291373X",
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_idref_victoire_data():
    """Concept IdRef `Victoire`, FRBNF15100021, the ark of `concept_gnd_sieg_data`."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_idref/idref-concept-v0.0.1.json",
        "authorized_access_point": "Victoire",
        "identifiedBy": [
            {"source": "IDREF", "type": "uri", "value": "http://www.idref.fr/109929764"},
            {"source": "BNF", "type": "uri", "value": "http://catalogue.bnf.fr/ark:/12148/cb151000210"},
            {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF15100021"},
        ],
        "pid": "109929764",
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_idref_epee_data():
    """Concept IdRef `Épée (sport)`, FRBNF12308292, the number of `concept_gnd_sieg_data`."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_idref/idref-concept-v0.0.1.json",
        "authorized_access_point": "Épée (sport)",
        "identifiedBy": [
            {"source": "IDREF", "type": "uri", "value": "http://www.idref.fr/031963382"},
            {"source": "BNF", "type": "uri", "value": "http://catalogue.bnf.fr/ark:/12148/cb12308292x"},
            {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF12308292"},
        ],
        "pid": "031963382",
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_idref_canon_data():
    """Concept IdRef `Canon (appareils-photo)`, FRBNF11931111.

    Live record https://mef.rero.ch/api/concepts/idref/027221970. Sixteen GND
    records close-match this one BNF number, one per camera model.
    """
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_idref/idref-concept-v0.0.1.json",
        "authorized_access_point": "Canon (appareils-photo)",
        "identifiedBy": [
            {"source": "IDREF", "type": "uri", "value": "http://www.idref.fr/027221970"},
            {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF11931111"},
        ],
        "pid": "027221970",
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_gnd_canon_data():
    """Concept GND records close-matching `Canon (appareils-photo)`.

    Three of the sixteen live records, https://mef.rero.ch/api/concepts/gnd/.
    """
    return [
        {
            "$schema": "https://mef.rero.ch/schemas/concepts_gnd/gnd-concept-v0.0.1.json",
            "authorized_access_point": authorized_access_point,
            "closeMatch": [
                {
                    "authorized_access_point": "Canon (appareils-photo)",
                    "identifiedBy": [{"source": "BNF", "type": "bf:Nbn", "value": "FRBNF11931111"}],
                    "source": "GND",
                }
            ],
            "pid": pid,
            "type": "bf:Topic",
        }
        for pid, authorized_access_point in (
            ("994914148", "Canon EOS 500D"),
            ("960401776", "Canon EOS 30"),
            ("041270053", "Canon (Marke)"),
        )
    ]


@pytest.fixture(scope="module")
def concept_gnd_spellings_data():
    """Concept GND record spelling one BNF number three different ways."""
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_gnd/gnd-concept-v0.0.1.json",
        "authorized_access_point": "Baum",
        "closeMatch": [
            {
                "authorized_access_point": "Arbres",
                "identifiedBy": [
                    {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF119347860"},
                    {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF11934786"},
                    {"type": "uri", "value": "https://data.bnf.fr/ark:/12148/cb11934786x"},
                ],
                "source": "BNF",
            }
        ],
        "pid": "040048454",
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_rero_ark_data():
    """Concept RERO `Poésie lyrique portugaise`, BNF number with RERO prefix.

    Live record https://mef.rero.ch/api/concepts/rero/A021020609. Its BNF
    number is prefixed `RERO` instead of `FRBNF`, but its BNF ark uri is the
    one of `concept_idref_ark_data`, character for character.
    """
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_rero/rero-concept-v0.0.1.json",
        "authorized_access_point": "Poésie lyrique portugaise",
        "broader": [{"authorized_access_point": "Poésie portugaise"}],
        "identifiedBy": [
            {"source": "RERO", "type": "bf:Local", "value": "A021020609"},
            {"source": "BNF", "type": "bf:Local", "value": "RERO119804685"},
            {"type": "uri", "value": "http://catalogue.bnf.fr/ark:/12148/cb119804687"},
        ],
        "pid": "A021020609",
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_idref_ark_data():
    """Concept IdRef `Poésie lyrique portugaise`, same BNF ark as RERO.

    Live record https://mef.rero.ch/api/concepts/idref/027851621.
    """
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_idref/idref-concept-v0.0.1.json",
        "authorized_access_point": "Poésie lyrique portugaise",
        "identifiedBy": [
            {"source": "IDREF", "type": "uri", "value": "http://www.idref.fr/027851621"},
            {"source": "BNF", "type": "uri", "value": "http://catalogue.bnf.fr/ark:/12148/cb119804687"},
            {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF11980468"},
        ],
        "pid": "027851621",
        "type": "bf:Topic",
    }


@pytest.fixture(scope="module")
def concept_gnd_check_char_data():
    """Concept GND `Westdeutsche`, FRBNF177016487 in exactMatch.

    One of the 16 GND records in `data/cognd.json` whose BNF number keeps its
    check character, so the raw value is 14 chars long.
    """
    return {
        "$schema": "https://mef.rero.ch/schemas/concepts_gnd/gnd-concept-v0.0.1.json",
        "authorized_access_point": "Westdeutsche",
        "exactMatch": [
            {
                "authorized_access_point": "Allemands de l'Ouest",
                "identifiedBy": [
                    {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)1332874800"},
                    {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF177016487"},
                    {"type": "uri", "value": "https://data.bnf.fr/ark:/12148/cb177016487"},
                ],
                "source": "GND",
            }
        ],
        "identifiedBy": [
            {"source": "GND", "type": "uri", "value": "http://d-nb.info/gnd/4279877-2"},
            {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)042798779"},
        ],
        "pid": "042798779",
        "type": "bf:Topic",
    }
