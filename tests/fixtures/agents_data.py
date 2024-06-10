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

"""Agents data."""

from os.path import dirname, join

import pytest


@pytest.fixture(scope="module")
def agent_gnd_data():
    """Agent GND record."""
    return {
        "$schema": "https://mef.rero.ch/schemas/agents_gnd/gnd-agent-v0.0.1.json",
        "identifier": "http://d-nb.info/gnd/12391664X",
        "pid": "12391664X",
        "type": "bf:Person",
        "variant_name": [
            "Cavaleriis, Joannes Baptista \u0098de\u009c",
            "Cavalleris, Joannes Baptista \u0098de\u009c",
            "Cavaleriis, Joanes Baptista \u0098de\u009c",
            "Cavalleriis, Johannes Baptista \u0098de\u009c",
            "Cavalerius, Johannes Battista \u0098de\u009c",
            "Cavallerys, Johannes Baptista \u0098de\u009c",
            "Cavaleriis, Johannes Baptista \u0098de\u009c",
            "Cavalieri, Giovanni Battista \u0098de\u009c",
            "Cavallieri, Giovan Battista \u0098de\u009c",
            "Cavalleriis, Johannes Battista",
            "Cavallerius, Johannes Baptista",
            "Cavallerius, Joannes Baptista",
            "Cavalleriis, Johannes Baptista",
            "Cavallieri, Giovanni Battista",
            "Cavaleriis, Giovanni Battista",
            "Cavalleriis, Io. Baptista \u0098de\u009c",
            "Cavallieri, Giovanni Battista \u0098de\u009c",
            "Cavalerijs, Io. Baptista \u0098de\u009c",
            "Cavallieri, Giovanni B.",
            "Cavaleriis, Joannes B. \u0098de\u009c",
            "Cavallerius, Jo. B. \u0098de\u009c",
            "Cavalleriis, Joannes Baptista \u0098de\u009c",
            "Cavallerijs, Baptista \u0098de\u009c",
            "Cavalleriis, Giovanni Battista \u0098de\u009c",
            "Cavallieri, Giovanbattista \u0098de\u009c",
            "Cavallerius, Io. Bap.ta",
            "Cavalierii, Johannes Baptista \u0098de\u009c",
        ],
        "authorized_access_point": "Cavalieri, Giovanni Battista, 1525-1601",
        "biographical_information": ["LoC-NA", "LCAuth"],
        "preferred_name": "Cavalieri, Giovanni Battista",
        "date_of_birth": "ca. 1525",
        "date_of_death": "1601",
    }


@pytest.fixture(scope="module")
def agent_gnd_redirect_data():
    """Agent GND record."""
    return {
        "$schema": "https://mef.rero.ch/schemas/agents_gnd/gnd-agent-v0.0.1.json",
        "identifier": "https://d-nb.info/gnd/GND_REDIRECT",
        "pid": "GND_REDIRECT",
        "type": "bf:Person",
        "authorized_access_point": "Cavalieri, Giovanni Battista, 1525-1601",
        "biographical_information": ["LoC-NA", "LCAuth"],
        "preferred_name": "Cavalieri, Giovanni Battista",
        "date_of_birth": "ca. 1525",
        "date_of_death": "1601",
        "relation_pid": {"type": "redirect_to", "value": "12391664X"},
    }


@pytest.fixture(scope="module")
def agent_gnd_response():
    """Agent RND online response."""
    return (
        '<record xmlns="http://www.loc.gov/MARC21/slim" type="Authority">'
        "<leader>00000nz  a2200000nc 4500</leader>"
        '<controlfield tag="001">12391664X</controlfield>'
        '<controlfield tag="003">DE-101</controlfield>'
        '<controlfield tag="005">20220311161448.0</controlfield>'
        '<controlfield tag="008">020708n||azznnaabn           | aaa    |c'
        "</controlfield>"
        '<datafield tag="024" ind1="7" ind2=" ">'
        '<subfield code="a">12391664X</subfield>'
        '<subfield code="0">http://d-nb.info/gnd/12391664X</subfield>'
        '<subfield code="2">gnd</subfield>'
        '</datafield> <datafield tag="035" ind1=" " ind2=" ">'
        '<subfield code="a">(DE-101)12391664X</subfield>'
        '</datafield> <datafield tag="035" ind1=" " ind2=" ">'
        '<subfield code="a">(DE-588)12391664X</subfield>'
        '</datafield> <datafield tag="035" ind1=" " ind2=" ">'
        '<subfield code="z">(DE-588a)12391664X</subfield>'
        '<subfield code="9">v:zg</subfield>'
        '</datafield> <datafield tag="035" ind1=" " ind2=" ">'
        '<subfield code="z">(DE-588c)4691051-7</subfield>'
        '<subfield code="9">v:zg</subfield>'
        '</datafield> <datafield tag="040" ind1=" " ind2=" ">'
        '<subfield code="a">DE-255</subfield>'
        '<subfield code="c">DE-255</subfield>'
        '<subfield code="9">r:DE-Y3</subfield>'
        '<subfield code="b">ger</subfield>'
        '<subfield code="d">9999</subfield>'
        '</datafield> <datafield tag="042" ind1=" " ind2=" ">'
        '<subfield code="a">gnd1</subfield>'
        '</datafield> <datafield tag="043" ind1=" " ind2=" ">'
        '<subfield code="c">XA-IT</subfield>'
        '</datafield> <datafield tag="065" ind1=" " ind2=" ">'
        '<subfield code="a">13.4p</subfield>'
        '<subfield code="2">sswd</subfield>'
        '</datafield> <datafield tag="075" ind1=" " ind2=" ">'
        '<subfield code="b">p</subfield>'
        '<subfield code="2">gndgen</subfield>'
        '</datafield> <datafield tag="075" ind1=" " ind2=" ">'
        '<subfield code="b">piz</subfield>'
        '<subfield code="2">gndspec</subfield>'
        '</datafield> <datafield tag="079" ind1=" " ind2="  ">'
        '<subfield code="a">g</subfield>'
        '<subfield code="q">s</subfield>'
        '<subfield code="q">a</subfield>'
        '<subfield code="q">f</subfield>'
        '</datafield> <datafield tag="100" ind1="1" ind2=" ">'
        '<subfield code="a">Cavalieri, Giovanni Battista</subfield>'
        '<subfield code="d">1525-1601</subfield>'
        '</datafield> <datafield tag="400" ind1="1" ind2=" ">'
        '<subfield code="a">Cavaleriis, Joannes Baptista \x98de\x9c'
        "</subfield>"
        '<subfield code="d">1525-1601</subfield>'
        '</datafield> <datafield tag="400" ind1="1" ind2=" ">'
        '<subfield code="a">Cavalleris, Joannes Baptista \x98de\x9c'
        "</subfield>"
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1" ind2=" ">'
        '<subfield code="a">Cavaleriis, Joanes Baptista \x98de\x9c'
        "</subfield>"
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1" ind2=" ">'
        '<subfield code="a">Cavalleriis, Johannes Baptista \x98de\x9c'
        "</subfield>"
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1" ind2=" ">'
        '<subfield code="a">Cavalerius, Johannes Battista \x98de\x9c'
        "</subfield>"
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1" ind2=" ">'
        '<subfield code="a">Cavallerys, Johannes Baptista \x98de\x9c'
        "</subfield>"
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavaleriis, Johannes Baptista  \x98de\x9c'
        "</subfield>"
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavalieri, Giovanni Battista  \x98de\x9c'
        "</subfield>"
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavallieri, Giovan Battista  \x98de\x9c'
        "</subfield>"
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavalleriis, Johannes  Battista</subfield>'
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavallerius, Johannes  Baptista</subfield>'
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavallerius, Joannes  Baptista</subfield>'
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavalleriis, Johannes  Baptista</subfield>'
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavallieri, Giovanni  Battista</subfield>'
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavaleriis, Giovanni  Battista</subfield>'
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavalleriis, Io. Baptista  \x98de\x9c'
        "</subfield>"
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavallieri, Giovanni Battista  \x98de\x9c'
        "</subfield>"
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavalerijs, Io. Baptista  \x98de\x9c'
        "</subfield>"
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavallieri, Giovanni B.</subfield>'
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavaleriis, Joannes B.  \x98de\x9c</subfield>'
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavallerius, Jo. B.  \x98de\x9c</subfield>'
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavalleriis, Joannes Baptista  \x98de\x9c'
        "</subfield>"
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavallerijs, Baptista  \x98de\x9c</subfield>'
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavalleriis, Giovanni Battista  \x98de\x9c'
        "</subfield>"
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavallieri, Giovanbattista  \x98de\x9c'
        "</subfield>"
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavallerius, Io. Bap.ta</subfield>'
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="400" ind1="1"  ind2="  ">'
        '<subfield code="a">Cavalierii, Johannes Baptista  \x98de\x9c'
        "</subfield>"
        '<subfield code="d">1525-1601</subfield>'
        "</datafield>"
        '<datafield tag="548" ind1=" "  ind2="  ">'
        '<subfield code="a">1525-1601</subfield>'
        '<subfield code="4">datl</subfield>'
        '<subfield code="4">'
        "https://d-nb.info/standards/elementset/gnd#dateOfBirthAndDeath"
        "</subfield>"
        '<subfield code="w">r</subfield>'
        '<subfield code="i">Lebensdaten</subfield>'
        '<subfield code="9">v:Geburtsjahr ca.</subfield>'
        "</datafield>"
        '<datafield tag="548" ind1="  " ind2="  ">'
        '<subfield code="a">ca. 1525-1601</subfield>'
        '<subfield code="4">datl</subfield>'
        '<subfield code="4">'
        "https://d-nb.info/standards/elementset/gnd#associatedDate"
        "</subfield>"
        '<subfield code="w">r</subfield>'
        '<subfield code="i">Lebensdaten</subfield>'
        "</datafield>"
        '<datafield tag="550" ind1=" "  ind2="  ">'
        '<subfield code="0">(DE-101)040372154</subfield>'
        '<subfield code="0">(DE-588)4037215-7</subfield>'
        '<subfield code="0">https://d-nb.info/gnd/4037215-7</subfield>'
        '<subfield code="a">Maler</subfield>'
        '<subfield code="4">berc</subfield>'
        '<subfield code="4">'
        "https://d-nb.info/standards/elementset/gnd#professionOrOccupation"
        "</subfield>"
        '<subfield code="w">r</subfield>'
        '<subfield code="i">Charakteristischer  Beruf</subfield>'
        "</datafield>"
        '<datafield tag="550" ind1=" " ind2="  ">'
        '<subfield  code="a">Maler</subfield>'
        '<subfield code="4">beru</subfield>'
        '<subfield code="4">'
        "https://d-nb.info/standards/elementset/gnd#professionOrOccupation"
        "</subfield>"
        '<subfield code="w">r</subfield>'
        '<subfield code="i">Beruf</subfield>'
        "</datafield>"
        '<datafield tag="550" ind1=" " ind2="   ">'
        '<subfield code="a">Kupferstecher</subfield>'
        '<subfield code="4">beru</subfield>'
        '<subfield code="4">'
        "https://d-nb.info/standards/elementset/gnd#professionOrOccupation"
        "</subfield>"
        '<subfield code="w">r</subfield>'
        '<subfield code="i">Beruf</subfield>'
        "</datafield>"
        '<datafield tag="667" ind1=" " ind2="   ">'
        '<subfield code="a">12</subfield>'
        "</datafield>"
        '<datafield tag="667" ind1=" "  ind2="  ">'
        '<subfield code="a">7</subfield>'
        "</datafield>"
        '<datafield tag="670"  ind1=" " ind2="  ">'
        '<subfield code="a">LoC-NA</subfield>'
        "</datafield>"
        '<datafield tag="670" ind1=" " ind2="  ">'
        '<subfield  code="a">LCAuth</subfield>'
        "</datafield>"
        '<datafield tag="672" ind1=" "  ind2="0 ">'
        '<subfield code="a">Cavalieri, Giovanni B.: '
        "Pontificum romanorum  Effigies</subfield>"
        '<subfield code="f">1580</subfield>'
        "</datafield>"
        '<datafield tag="672" ind1=" " ind2="0 ">'
        '<subfield code="a">Cavalieri, Giovanni B.:  '
        "Pontificum romanorum Effigies</subfield>"
        '<subfield code="f">1585</subfield>'
        "</datafield>"
        '<datafield tag="672" ind1=" "  ind2="0 ">'
        '<subfield code="a">Cavalieri, Giovanni B.: '
        "Pontificum romanorum  Effigies</subfield>"
        '<subfield code="f">1591</subfield>'
        "</datafield>"
        '<datafield tag="672" ind1=" " ind2="0 ">'
        '<subfield code="a">Cavalieri, Giovanni B.:  '
        "Antiquarum Statuarum urbis Romae liber</subfield>"
        '<subfield code="f">1570</subfield>'
        "</datafield>"
        '<datafield tag="672" ind1=" "  ind2="0 ">'
        '<subfield code="a">Cavalieri, Giovanni B.: '
        "Antiquae statuae Urbis  Romae</subfield>"
        '<subfield code="f">1585</subfield>'
        "</datafield>"
        '<datafield tag="672" ind1=" " ind2="0 ">'
        '<subfield code="a">Circignano, Niccolò: SS.  '
        "Martirum triumphi. - s.a.</subfield>"
        "</datafield>"
        '<datafield tag="672" ind1="  " ind2="0 ">'
        '<subfield code="a">Ciccarelli, Antonio: Le Vite de  Pontifici'
        "</subfield>"
        '<subfield code="f">1587</subfield>'
        "</datafield>"
        '<datafield tag="672" ind1=" " ind2="0 ">'
        '<subfield code="a">Ciccarelli, Antonio: Le Vite  de Pontefici'
        "</subfield>"
        '<subfield code="f">1588</subfield>'
        "</datafield>"
        '<datafield tag="672" ind1=" "  ind2="0 ">'
        '<subfield code="a">Cavalieri, Giovanni B.: '
        "Antiquarum statuarum  urbis Romae ... liber.</subfield>"
        "</datafield>"
        '<datafield tag="672" ind1=" "  ind2="0 ">'
        '<subfield code="a">Cavalieri, Giovanni B.: '
        "Antiquarum statuarum  urbis Romae</subfield>"
        "</datafield>"
        '<datafield tag="678" ind1=" " ind2="   ">'
        '<subfield code="b">Maler, Kupferstecher</subfield>'
        "</datafield>"
        '<datafield tag="913" ind1=" " ind2="  ">'
        '<subfield code="S">pnd</subfield>'
        '<subfield code="i">a</subfield>'
        '<subfield code="a">Cavalieri, Giovanni  Battista</subfield>'
        '<subfield code="0">(DE-588a)12391664X</subfield>'
        "</datafield></record></metadata>"
        "</record>"
    )


@pytest.fixture(scope="module")
def agent_rero_data():
    """Agent RERO record."""
    return {
        "$schema": "https://mef.rero.ch/schemas/agents_rero/rero-agent-v0.0.1.json",
        "type": "bf:Person",
        "authorized_access_point": "Cavalieri, Giovanni Battista,, ca.1525-1601",
        "date_of_birth": "ca.1525-1601",
        "biographical_information": ["Graveur, dessinateur et \u00e9diteur"],
        "variant_name": [
            "De Cavalieri, Giovanni Battista,",
            "Cavalleriis, Baptista de,",
            "Cavalleriis, Giovanni Battista de,",
            "Cavalieri, Gianbattista,",
        ],
        "identifier": "https://data.rero.ch/02-A023655346",
        "pid": "A023655346",
        "preferred_name": "Cavalieri, Giovanni Battista,",
    }


@pytest.fixture(scope="module")
def agent_rero_response():
    """Agent RERO online response."""
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<collection xmlns="http://www.loc.gov/MARC21/slim">'
        b"<record>"
        b" <leader>00632nz  a2200217n  4500</leader>"
        b' <controlfield tag="001">23655346</controlfield>'
        b' <controlfield tag="003">RERO</controlfield>'
        b' <controlfield tag="005">20200907080040.0</controlfield>'
        b' <controlfield tag="008">'
        b"130905 | acn||abbn           n aaa d</controlfield>"
        b' <datafield tag="024" ind1="7" ind2=" ">'
        b'  <subfield code="a">068979401</subfield>'
        b'  <subfield code="2">idref</subfield>'
        b" </datafield>"
        b' <datafield tag="035" ind1=" " ind2=" ">'
        b'  <subfield code="a">A023655346</subfield>'
        b" </datafield>"
        b' <datafield tag="039" ind1=" " ind2="9">'
        b'  <subfield code="a">202009070800</subfield>'
        b'  <subfield code="b">VLOAD</subfield>'
        b'  <subfield code="c">202009060904</subfield>'
        b'  <subfield code="d">VLOAD</subfield>'
        b'  <subfield code="y">201309051208</subfield>'
        b'  <subfield code="z">0060</subfield>'
        b" </datafield>"
        b' <datafield tag="040" ind1=" " ind2=" ">'
        b'  <subfield code="a">RERO frbcuc</subfield>'
        b" </datafield>"
        b' <datafield tag="100" ind1="1" ind2=" ">'
        b'  <subfield code="a">Cavalieri, Giovanni Battista,</subfield>'
        b'  <subfield code="d">ca.1525-1601</subfield>'
        b" </datafield>"
        b' <datafield tag="400" ind1="1" ind2=" ">'
        b'  <subfield code="a">De Cavalieri, Giovanni Battista,</subfield>'
        b'  <subfield code="d">ca.1525-1601</subfield>'
        b" </datafield>"
        b' <datafield tag="400" ind1="1" ind2=" ">'
        b'  <subfield code="a">Cavalleriis, Baptista de,</subfield>'
        b'  <subfield code="d">ca.1525-1601</subfield>'
        b" </datafield>"
        b' <datafield tag="400" ind1="1" ind2=" ">'
        b'  <subfield code="a">Cavalleriis, Giovanni Battista de,</subfield>'
        b'  <subfield code="d">ca.1525-1601</subfield>'
        b" </datafield>"
        b' <datafield tag="400" ind1="1" ind2=" ">'
        b'  <subfield code="a">Cavalieri, Gianbattista,</subfield>'
        b'  <subfield code="d">ca.1525-1601</subfield>'
        b" </datafield>"
        b' <datafield tag="670" ind1=" " ind2=" ">'
        b'  <subfield code="a">LoCNA, 05.09.2013</subfield>'
        b" </datafield>"
        b' <datafield tag="670" ind1=" " ind2=" ">'
        b'  <subfield code="a">BnF, 05.09.2013</subfield>'
        b" </datafield>"
        b' <datafield tag="680" ind1=" " ind2=" ">'
        b'  <subfield code="a">'
        b"Graveur, dessinateur et \xc3\xa9diteur</subfield>"
        b" </datafield>"
        b"</record>"
        b"</collection>"
    )


@pytest.fixture(scope="module")
def agent_idref_data():
    """Agent IDREF record."""
    return {
        "pid": "069774331",
        "type": "bf:Person",
        "date_of_birth": "....",
        "date_of_death": "1540",
        "language": ["fre"],
        "identifier": "https://www.idref.fr/069774331",
        "biographical_information": ["Grammairien"],
        "preferred_name": "Briss\u00e9, Nicolas, grammairien",
        "authorized_access_point": "Briss\u00e9, Nicolas, ....-1540, grammairien",
        "gender": "male",
        "$schema": "https://mef.rero.ch/schemas/agents_idref/idref-agent-v0.0.1.json",
    }


@pytest.fixture(scope="module")
def agent_idref_redirect_data():
    """Agent IDREF record."""
    return {
        "pid": "IDREF_REDIRECT",
        "type": "bf:Person",
        "date_of_birth": "....",
        "date_of_death": "1540",
        "language": ["fre"],
        "identifier": "https://www.idref.fr/IDREF_REDIRECT",
        "preferred_name": "Briss\u00e9, Nicolas, grammairien",
        "authorized_access_point": "Briss\u00e9, Nicolas, ....-1540, grammairien",
        "gender": "male",
        "$schema": "https://mef.rero.ch/schemas/agents_idref/idref-agent-v0.0.1.json",
        "relation_pid": {"type": "redirect_from", "value": "069774331"},
    }


@pytest.fixture(scope="module")
def agent_mef_data():
    """Agent MEF record."""
    return {
        "$schema": "https://mef.rero.ch/schemas/mef/mef-v0.0.1.json",
        "gnd": {"$ref": "https://mef.rero.ch/api/agents/gnd/12391664X"},
        "rero": {"$ref": "https://mef.rero.ch/api/agents/rero/A023655346"},
        "idref": {"$ref": "https://mef.rero.ch/api/agents/idref/069774331"},
        "viaf_pid": "66739143",
    }


@pytest.fixture(scope="module")
def agent_mef_gnd_redirect_data():
    """Agent MEF record."""
    return {
        "$schema": "https://mef.rero.ch/schemas/mef/mef-v0.0.1.json",
        "gnd": {"$ref": "https://mef.rero.ch/api/agents/gnd/GND_REDIRECT"},
        "viaf_pid": "VIAF_REDIRECT",
        "type": "bf:Person",
    }


@pytest.fixture(scope="module")
def agent_mef_idref_redirect_data():
    """Agent MEF record."""
    return {
        "$schema": "https://mef.rero.ch/schemas/mef/mef-v0.0.1.json",
        "gnd": {"$ref": "https://mef.rero.ch/api/agents/gnd/12391664X"},
        "rero": {"$ref": "https://mef.rero.ch/api/agents/rero/A023655346"},
        "idref": {"$ref": "https://mef.rero.ch/api/agents/idref/IDREF_REDIRECT"},
        "viaf_pid": "66739143",
        "type": "bf:Person",
    }


@pytest.fixture(scope="module")
def agent_viaf_data():
    """Agent VIAF record."""
    return {
        "$schema": "https://mef.rero.ch/schemas/viaf/viaf-v0.0.1.json",
        "pid": "66739143",
        "gnd_pid": "12391664X",
        "rero_pid": "A023655346",
        "idref_pid": "069774331",
    }


@pytest.fixture(scope="module")
def agent_viaf_gnd_redirect_data():
    """Agent VIAF record."""
    return {
        "$schema": "https://mef.rero.ch/schemas/viaf/viaf-v0.0.1.json",
        "pid": "VIAF_GND_REDIRECT",
        "gnd_pid": "GND_REDIRECT",
    }


@pytest.fixture(scope="module")
def agent_viaf_idref_redirect_data():
    """Agent VIAF record."""
    return {
        "$schema": "https://mef.rero.ch/schemas/viaf/viaf-v0.0.1.json",
        "pid": "VIAF_IDREF_REDIRECT",
        "gnd_pid": "12391664X",
        "rero_pid": "IDREF_REDIRECT",
        "idref_pid": "069774331",
    }


@pytest.fixture(scope="module")
def agent_viaf_online_response():
    """Agent VIAF online responserecord."""
    return {
        "@xmlns": "http://viaf.org/viaf/terms#",
        "Document": {
            "@about": "http://viaf.org/viaf/124294761/",
            "inDataset": {"@resource": "http://viaf.org/viaf/data"},
            "primaryTopic": {"@resource": "http://viaf.org/viaf/124294761"},
        },
        "RecFormats": {
            "data": {
                "@count": "6",
                "sources": {
                    "s": ["BNF", "BAV"],
                    "sid": ["BNF|12544283", "BAV|493_4879"],
                },
                "text": "am",
            }
        },
        "RelatorCodes": {
            "data": [
                {
                    "@count": "2",
                    "sources": {"s": "BNF", "sid": "BNF|12544283"},
                    "text": "070",
                },
                {
                    "@count": "3",
                    "sources": {"s": "BNF", "sid": "BNF|12544283"},
                    "text": "340",
                },
            ]
        },
        "birthDate": "0",
        "coauthors": {
            "data": [
                {
                    "@count": "2",
                    "@tag": "950",
                    "sources": {"s": "BNF", "sid": "BNF|12544283"},
                    "text": "Hugo, Victor 1802-1885",
                },
                {
                    "@count": "1",
                    "@tag": "951",
                    "sources": {"s": "BNF", "sid": "BNF|12544283"},
                    "text": "Socie\\u0301te\\u0301 des gens de lettres de "
                    "France Paris",
                },
                {
                    "@count": "1",
                    "@tag": "951",
                    "sources": {"s": "BNF", "sid": "BNF|12544283"},
                    "text": "Socie\\u0301te\\u0301 des gens de lettres France",
                },
                {
                    "@count": "1",
                    "@tag": "950",
                    "sources": {"s": "BNF", "sid": "BNF|12544283"},
                    "text": "Celliez, Henry 1806-1884",
                },
            ]
        },
        "countries": {
            "data": {
                "@count": "6",
                "@scaled": "3",
                "sources": {
                    "s": ["BNF", "BAV"],
                    "sid": ["BNF|12544283", "BAV|493_4879"],
                },
                "text": "FR",
            }
        },
        "creationtime": "2022-12-11T22:19:27.310129+00:00",
        "dateType": "lived",
        "dates": {
            "@max": "187",
            "@min": "187",
            "date": {"#text": "187", "@count": "1", "@scaled": "0.00"},
        },
        "deathDate": "0",
        "fixed": {"gender": "u"},
        "foaf": "http://xmlns.com/foaf/0.1/",
        "history": {
            "ht": [
                {"@recid": "SUDOC|076515788", "@time": "2014-12-17T15:43:51+00:00"},
                {"@recid": "DNB|969004222", "@time": "2014-12-17T15:43:51+00:00"},
                {"@recid": "BNF|11717946", "@time": "2016-01-31T03:15:00.183026+00:00"},
                {"@recid": "BNF|12544283", "@time": "2016-01-31T03:15:00.229544+00:00"},
                {"@recid": "BAV|493_4879", "@time": "2020-07-14T14:21:02.860830+00:00"},
            ]
        },
        "languageOfEntity": {"data": {"sources": {"s": "BNF"}, "text": "mul"}},
        "length": "62",
        "mainHeadings": {
            "data": {
                "sources": {
                    "s": ["SUDOC", "DNB", "BAV", "BNF"],
                    "sid": [
                        "SUDOC|076515788",
                        "DNB|969004222",
                        "BAV|493_4879",
                        "BNF|12544283",
                    ],
                },
                "text": "Congr\\u00e8s litt\\u00e9raire international "
                "(1878 : Paris)",
            },
            "mainHeadingEl": [
                {
                    "datafield": {
                        "@dtype": "MARC21",
                        "@ind1": "2",
                        "@ind2": " ",
                        "@tag": "111",
                        "subfield": [
                            {
                                "#text": "Congre\\u0300s Litte\\u0301raire "
                                "International",
                                "@code": "a",
                            },
                            {"#text": "1878", "@code": "d"},
                            {"#text": "Paris", "@code": "c"},
                        ],
                    },
                    "id": "DNB|969004222",
                    "links": {
                        "link": [
                            {"#text": "SUDOC|076515788", "ns1:match": None},
                            {"#text": "BNF|12544283", "ns1:match": None},
                            {"#text": "BAV|493_4879", "ns1:match": None},
                        ]
                    },
                    "sources": {"s": "DNB", "sid": "DNB|969004222"},
                },
                {
                    "datafield": {
                        "@dtype": "MARC21",
                        "@ind1": "2",
                        "@ind2": " ",
                        "@tag": "111",
                        "subfield": [
                            {
                                "#text": "Congre\\u0300s litte\\u0301raire "
                                "international",
                                "@code": "a",
                            },
                            {"#text": "(1878 :", "@code": "d"},
                            {"#text": "Paris)", "@code": "c"},
                        ],
                    },
                    "id": "SUDOC|076515788",
                    "links": {
                        "link": [
                            {"#text": "BNF|12544283", "ns1:match": None},
                            {"#text": "BAV|493_4879", "ns1:match": None},
                            {"#text": "DNB|969004222", "ns1:match": None},
                        ]
                    },
                    "sources": {"s": "SUDOC", "sid": "SUDOC|076515788"},
                },
                {
                    "datafield": {
                        "@dtype": "UNIMARC",
                        "@ind1": "|",
                        "@ind2": "|",
                        "@tag": "210",
                        "subfield": [
                            {"#text": "ba0yba0y", "@code": "7"},
                            {"#text": "frefre", "@code": "8"},
                            {"#text": "20", "@code": "9"},
                            {
                                "#text": "Congre\\u0300s litte\\u0301raire "
                                "international",
                                "@code": "a",
                            },
                            {"#text": "1878", "@code": "f"},
                            {"#text": "Paris", "@code": "e"},
                        ],
                    },
                    "id": "BNF|12544283",
                    "links": {
                        "link": [
                            {"#text": "SUDOC|076515788", "ns1:match": None},
                            {"#text": "DNB|969004222", "ns1:match": None},
                            {"#text": "BAV|493_4879", "ns1:match": None},
                        ]
                    },
                    "sources": {"s": "BNF", "sid": "BNF|12544283"},
                },
                {
                    "datafield": {
                        "@dtype": "MARC21",
                        "@ind1": "2",
                        "@ind2": " ",
                        "@tag": "111",
                        "subfield": [
                            {
                                "#text": "Congr\\u00e8s litt\\u00e9raire "
                                "international",
                                "@code": "a",
                            },
                            {"#text": "(1878 :", "@code": "d"},
                            {"#text": "Paris)", "@code": "c"},
                        ],
                    },
                    "id": "BAV|493_4879",
                    "links": {
                        "link": [
                            {"#text": "SUDOC|076515788", "ns1:match": None},
                            {"#text": "BNF|12544283", "ns1:match": None},
                            {"#text": "DNB|969004222", "ns1:match": None},
                        ]
                    },
                    "sources": {"s": "BAV", "sid": "BAV|493_4879"},
                },
            ],
        },
        "nameType": "Corporate",
        "nationalityOfEntity": {
            "data": [
                {"sources": {"s": "BNF"}, "text": "ZZ"},
                {"sources": {"s": "DNB"}, "text": "FR"},
            ]
        },
        "ns1": "http://viaf.org/viaf/terms#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "publishers": {
            "data": [
                {
                    "@count": "3",
                    "sources": {
                        "s": ["BNF", "BAV"],
                        "sid": ["BNF|12544283", "BAV|493_4879"],
                    },
                    "text": "bureaux de la Socie\\u0301te\\u0301 des gens de "
                    "lettres",
                },
                {
                    "@count": "2",
                    "sources": {"s": "BNF", "sid": "BNF|12544283"},
                    "text": "Calmann Le\\u0301vy, e\\u0301diteur",
                },
                {
                    "@count": "1",
                    "sources": {"s": "BNF", "sid": "BNF|12544283"},
                    "text": "impr. de A. Chaix",
                },
            ]
        },
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "sources": {
            "source": [
                {"#text": "DNB|969004222", "@nsid": "http://d-nb.info/gnd/1248506-8"},
                {"#text": "SUDOC|076515788", "@nsid": "076515788"},
                {
                    "#text": "BNF|12544283",
                    "@nsid": "http://catalogue.bnf.fr/ark:/12148/cb125442835",
                },
                {"#text": "BAV|493_4879", "@nsid": "493/4879"},
            ]
        },
        "titles": {
            "work": [
                {
                    "sources": {"s": "BNF", "sid": "BNF|12544283"},
                    "title": "domaine public payant",
                },
                {
                    "sources": {"s": "BNF", "sid": "BNF|12544283"},
                    "title": "Proposition d'un voeu a\\u0300 exprimer par le "
                    "Congre\\u0300s, relativement au droit des auteurs sur "
                    "leurs oeuvres publie\\u0301es en pays e\\u0301tranger, "
                    "par Henry Celliez, lue a\\u0300 la 2e section du "
                    "Congre\\u0300s le 13 juin...",
                },
                {
                    "sources": {
                        "s": ["BNF", "BAV"],
                        "sid": ["BNF|12544283", "BAV|493_4879"],
                    },
                    "title": "Socie\\u0301te\\u0301 des gens de lettres de "
                    "France. Congre\\u0300s litte\\u0301raire international "
                    "de Paris, 1878, pre\\u0301sidence de Victor Hugo. "
                    "Comptes rendus in extenso et documents",
                },
            ]
        },
        "viafID": "124294761",
        "void": "http://rdfs.org/ns/void#",
        "x400s": {
            "x400": {
                "datafield": {
                    "@dtype": "MARC21",
                    "@ind1": "2",
                    "@ind2": " ",
                    "@tag": "411",
                    "normalized": "congres litteraire international de la "
                    "protection de la propriete litteraire dans les rapports "
                    "internationaux",
                    "subfield": {
                        "#text": "Congre\\u0300s litte\\u0301raire "
                        "international de la protection de la "
                        "proprie\\u0301te\\u0301 litte\\u0301raire dans les "
                        "rapports internationaux",
                        "@code": "a",
                    },
                },
                "sources": {"s": "SUDOC", "sid": "SUDOC|076515788"},
            }
        },
        "x500s": {
            "x500": {
                "@viafLink": "240792131",
                "datafield": {
                    "@dtype": "MARC21",
                    "@ind1": " ",
                    "@ind2": " ",
                    "@tag": "551",
                    "normalized": "paris",
                    "subfield": {"#text": "Paris", "@code": "a"},
                },
                "sources": {"s": "DNB", "sid": "DNB|969004222"},
            }
        },
    }


@pytest.fixture(scope="module")
def aggnd_data_139205527():
    """GND JSON for 139205527."""
    return {
        "authorized_access_point": "Parisi, Chiara",
        "type": "bf:Person",
        "country_associated": "it",
        "gender": "female",
        "identifier": "http://d-nb.info/gnd/139205527",
        "identifiedBy": [
            {"source": "GND", "type": "uri", "value": "http://d-nb.info/gnd/139205527"}
        ],
        "pid": "139205527",
        "preferred_name": "Parisi, Chiara",
    }


@pytest.fixture(scope="module")
def aggnd_oai_139205527():
    """OAIPMH xml response for GND 139205527."""
    file_name = join(dirname(__file__), "../data/aggnd_oai_139205527.xml")
    with open(file_name, "rb") as file:
        return file.read()


@pytest.fixture(scope="module")
def aggnd_oai_list_records():
    """OAIPMH xml list records."""
    file_name = join(dirname(__file__), "../data/aggnd_oai_list_records.xml")
    with open(file_name, "rb") as file:
        return file.read()


@pytest.fixture(scope="module")
def aggnd_oai_list_records_empty():
    """OAIPMH xml list records empty."""
    file_name = join(dirname(__file__), "../data/aggnd_oai_list_records_empty.xml")
    with open(file_name, "rb") as file:
        return file.read()
