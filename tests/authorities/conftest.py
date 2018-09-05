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

"""Pytest configuration."""

import pytest


@pytest.fixture(scope='session')
def empty_mef_record():
    """Empty MEF record."""
    json_record = {}
    return json_record


@pytest.fixture(scope='session')
def mef_record():
    """MEF record."""
    record = {
        "bnf": {"$ref": "http://mef.test.rero.ch/api/bnf/10008312"},
        "gnd": {"$ref": "http://mef.test.rero.ch/api/gnd/12391664X"},
        "rero": {"$ref": "http://mef.test.rero.ch/api/rero/A023655346"},
        "viaf_pid": "66739143"
    }
    return record


@pytest.fixture(scope='session')
def bnf_record():
    """BNF record."""
    record = {
        "preferred_name_for_person": "Cavalieri, Giovanni-Battista",
        "gender": "male",
        "date_of_birth": "1525",
        "language_of_person": [
          "lat"
        ],
        "authorized_access_point_representing_a_person":
            "Cavalieri, Giovanni-Battista, 1525?-1601",
        "variant_name_for_person": [
            "Cavaleriis, Joannes-Baptista de",
            "Cavalieri, Giovanni-Battista de'",
            "Cavalleri, Giovanni-Battista de",
            "Cavalleriis, Giovanni-Battista de",
            "Cavalleriis, Joannes-Baptista de",
            "De Cavaleriis, Giovanni-Battista",
            "De' Cavalieri, Giovanni-Battista",
            "De' Cavalleri, Giovanni-Battista",
            "De Cavalleriis, Giovanni-Battista"
        ],
        "biographical_information": [
            "Graveur, dessinateur et \u00e9diteur"
        ],
        "date_of_death": "?",
        "md5": "5103006dfbe6d9579856cfdd495e8d98",
        "identifier_for_person": "10008312"
    }
    return record


@pytest.fixture(scope='session')
def gnd_record():
    """GND record."""
    record = {
        "identifier_for_person": "12391664X",
        "variant_name_for_person": [
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
            "Cavalierii, Johannes Baptista \u0098de\u009c"
        ],
        "authorized_access_point_representing_a_person":
            "Cavalieri, Giovanni Battista, 1525-1601",
        "biographical_information": [
            "LoC-NA",
            "LCAuth"
        ],
        "preferred_name_for_person": "Cavalieri, Giovanni Battista",
        "date_of_birth": "ca. 1525",
        "date_of_death": "1601"
    }
    return record


@pytest.fixture(scope='session')
def rero_record():
    """RERO record."""
    record = {
        "authorized_access_point_representing_a_person":
            "Cavalieri, Giovanni Battista,, ca.1525-1601",
        "date_of_birth": "ca.1525-1601",
        "biographical_information": [
            "Graveur, dessinateur et \u00e9diteur"
        ],
        "variant_name_for_person": [
            "De Cavalieri, Giovanni Battista,",
            "Cavalleriis, Baptista de,",
            "Cavalleriis, Giovanni Battista de,",
            "Cavalieri, Gianbattista,"
        ],
        "identifier_for_person": "A023655346",
        "preferred_name_for_person": "Cavalieri, Giovanni Battista,"
    }
    return record
