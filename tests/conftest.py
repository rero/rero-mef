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

"""Common pytest fixtures and plugins."""

import pytest

pytest_plugins = ("celery.contrib.pytest", )


@pytest.fixture(scope='module')
def es(appctx):
    """Setup and teardown all registered Elasticsearch indices.

    Scope: module
    This fixture will create all registered indexes in Elasticsearch and remove
    once done. Fixtures that perform changes (e.g. index or remove documents),
    should used the function-scoped :py:data:`es_clear` fixture to leave the
    indexes clean for the following tests.
    """
    from invenio_search import current_search, current_search_client

    current_search_client.indices.delete_template('*')
    list(current_search.put_templates())

    list(current_search.delete(ignore=[404]))
    list(current_search.create())
    current_search_client.indices.refresh()

    try:
        yield current_search_client
    finally:
        current_search_client.indices.delete(index='*')
        current_search_client.indices.delete_template('*')


@pytest.fixture(scope='module')
def app_config(app_config):
    """Create temporary instance dir for each test."""
    app_config['CELERY_BROKER_URL'] = 'memory://'
    app_config['RATELIMIT_STORAGE_URL'] = 'memory://'
    app_config['CACHE_TYPE'] = 'simple'
    app_config['ACCOUNTS_SESSION_REDIS_URL'] = 'redis://localhost:6379/1'
    app_config['SEARCH_ELASTIC_HOSTS'] = None
    app_config['CELERY_CACHE_BACKEND'] = "memory"
    app_config['CELERY_RESULT_BACKEND'] = "cache"
    app_config['CELERY_TASK_ALWAYS_EAGER'] = True
    app_config['CELERY_TASK_EAGER_PROPAGATES'] = True
    return app_config


@pytest.fixture(scope='session')
def agent_mef_record():
    """Agent MEF record."""
    record = {
        "$schema": "https://mef.rero.ch/schemas/mef/mef-v0.0.1.json",
        "gnd": {"$ref": "https://mef.rero.ch/api/gnd/12391664X"},
        "rero": {"$ref": "https://mef.rero.ch/api/rero/A023655346"},
        "idref": {"$ref": "https://mef.rero.ch/api/idref/069774331"},
        "viaf_pid": "66739143"
    }
    return record


@pytest.fixture(scope='session')
def agent_viaf_record():
    """Agent VIAF record."""
    record = {
        "$schema": "https://mef.rero.ch/schemas/viaf/viaf-v0.0.1.json",
        "pid": "66739143",
        "gnd_pid": "12391664X",
        "rero_pid": "A023655346",
        "idref_pid": "069774331"
    }
    return record


@pytest.fixture(scope='session')
def agent_gnd_record():
    """Agent GND record."""
    record = {
        "$schema":
        "https://mef.rero.ch/schemas/agents_gnd/gnd-agent-v0.0.1.json",
        "identifier": "http://d-nb.info/gnd/12391664X",
        "pid": "12391664X",
        "bf:Agent": "bf:Person",
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
            "Cavalierii, Johannes Baptista \u0098de\u009c"
        ],
        "authorized_access_point": "Cavalieri, Giovanni Battista, 1525-1601",
        "biographical_information": [
            "LoC-NA",
            "LCAuth"
        ],
        "preferred_name": "Cavalieri, Giovanni Battista",
        "date_of_birth": "ca. 1525",
        "date_of_death": "1601"
    }
    return record


@pytest.fixture(scope='session')
def agent_rero_record():
    """Agent RERO record."""
    record = {
        "$schema":
        "https://mef.rero.ch/schemas/agents_rero/rero-agent-v0.0.1.json",
        "bf:Agent": "bf:Person",
        "authorized_access_point":
            "Cavalieri, Giovanni Battista,, ca.1525-1601",
        "date_of_birth": "ca.1525-1601",
        "biographical_information": [
            "Graveur, dessinateur et \u00e9diteur"
        ],
        "variant_name": [
            "De Cavalieri, Giovanni Battista,",
            "Cavalleriis, Baptista de,",
            "Cavalleriis, Giovanni Battista de,",
            "Cavalieri, Gianbattista,"
        ],
        "identifier": "http://data.rero.ch/02-A023655346",
        "pid": "A023655346",
        "preferred_name": "Cavalieri, Giovanni Battista,"
    }
    return record


@pytest.fixture(scope='session')
def agent_idref_record():
    """Agent IDREF record."""
    record = {
        "pid": "069774331",
        "bf:Agent": "bf:Person",
        "date_of_birth": "....",
        "date_of_death": "1540",
        "language": ["fre"],
        "identifier": "http://www.idref.fr/069774331",
        "biographical_information": [
          "Grammairien"
        ],
        "preferred_name": "Briss\u00e9, Nicolas, grammairien",
        "authorized_access_point":
            "Briss\u00e9, Nicolas, ....-1540, grammairien",
        "gender": "male",
        "$schema":
            "https://mef.rero.ch/schemas/agents_idref/idref-agent-v0.0.1.json"
    }
    return record


@pytest.fixture(scope='session')
def concept_rero_record():
    """Concept RERO record."""
    record = {
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
    return record
