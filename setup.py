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

"""
MEF (Multilingual Entity File) server with records for persons, works, etc.
for reuse in integrated library systems (ILS).
"""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()

INVENIO_VERSION = "3.4.1"

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('rero_mef', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='rero-mef',
    version=version,
    description=__doc__,
    long_description=readme,
    keywords='rero-mef Invenio',
    license='GPL',
    author='RERO',
    author_email='software@rero.ch',
    url='https://github.com/rero/rero-mef',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_celery.tasks': [
            'rero_mef = rero_mef.tasks',
            'agents = rero_mef.agents.tasks',
            'idref = rero_mef.agents.idref.tasks',
            'gnd = rero_mef.agents.gnd.tasks',
        ],
        'console_scripts': [
            'rero-mef = invenio_app.cli:cli',
        ],
        'invenio_assets.webpack': [
            'rero_mef_css = rero_mef.theme.webpack:theme',
        ],
        'invenio_base.apps': [
            'rero-mef = rero_mef.ext:REROMEFAPP',
        ],
        'invenio_base.blueprints': [
            'rero_mef = rero_mef.theme.views:blueprint',
        ],
        'invenio_config.module': [
            'rero_mef = rero_mef.config',
        ],
        'invenio_db.models': [
            'mef = rero_mef.agents.mef.models',
            'viaf = rero_mef.agents.viaf.models',
            'agents_gnd = rero_mef.agents.gnd.models',
            'agents_idref = rero_mef.agents.idref.models',
            'agents_rero = rero_mef.agents.rero.models',
            'concepts_mef = rero_mef.concepts.mef.models',
            'concepts_rero = rero_mef.concepts.rero.models',
        ],
        'invenio_pidstore.minters': [
            'mef_id = rero_mef.agents.mef.minters:mef_id_minter',
            'viaf_id = rero_mef.agents.viaf.minters:viaf_id_minter',
            'agent_gnd_id = rero_mef.agents.gnd.minters:gnd_id_minter',
            'agent_idref_id = rero_mef.agents.idref.minters:idref_id_minter',
            'agent_rero_id = rero_mef.agents.rero.minters:rero_id_minter',
            'concept_mef_id = rero_mef.concepts.mef.minters:mef_id_minter',
            'concept_rero_id = rero_mef.concepts.rero.minters:rero_id_minter',
        ],
        'invenio_pidstore.fetchers': [
            'mef_id = rero_mef.agents.mef.fetchers:mef_id_fetcher',
            'viaf_id = rero_mef.agents.viaf.fetchers:viaf_id_fetcher',
            'agent_gnd_id = rero_mef.agents.gnd.fetchers:gnd_id_fetcher',
            'agent_idref_id = rero_mef.agents.idref.fetchers:idref_id_fetcher',
            'agent_rero_id = rero_mef.agents.rero.fetchers:rero_id_fetcher',
            'concept_mef_id = rero_mef.concepts.mef.fetchers:mef_id_fetcher',
            'concept_rero_id = rero_mef.concepts.rero.fetchers:rero_id_fetcher',
        ],
        'invenio_jsonschemas.schemas': [
            'common = rero_mef.jsonschemas',
            'mef = rero_mef.agents.mef.jsonschemas',
            'viaf = rero_mef.agents.viaf.jsonschemas',
            'agents_gnd = rero_mef.agents.gnd.jsonschemas',
            'agents_idref = rero_mef.agents.idref.jsonschemas',
            'agents_rero = rero_mef.agents.rero.jsonschemas',
            'cocepts_mef = rero_mef.concepts.mef.jsonschemas',
            'cocepts_rero = rero_mef.concepts.rero.jsonschemas',
        ],
        'invenio_search.mappings': [
            'mef = rero_mef.agents.mef.mappings',
            'viaf = rero_mef.agents.viaf.mappings',
            'agents_gnd = rero_mef.agents.gnd.mappings',
            'agents_idref = rero_mef.agents.idref.mappings',
            'agents_rero = rero_mef.agents.rero.mappings',
            'concepts_mef = rero_mef.concepts.mef.mappings',
            'concepts_rero = rero_mef.concepts.rero.mappings',
        ],
        'invenio_records.jsonresolver': [
            'mef = rero_mef.agents.mef.jsonresolvers.mef_resolver',
            'viaf = rero_mef.agents.viaf.jsonresolvers.viaf_resolver',
            'agents_gnd = rero_mef.agents.gnd.jsonresolvers.gnd_resolver',
            'agents_idref = rero_mef.agents.idref.jsonresolvers.idref_resolver',
            'agents_rero = rero_mef.agents.rero.jsonresolvers.rero_resolver',
            'concepts_mef = rero_mef.concepts.mef.jsonresolvers.mef_resolver',
            'concepts_rero = rero_mef.concepts.rero.jsonresolvers.rero_resolver',
        ],
        'invenio_base.api_blueprints': [
            'api_rero_mef = rero_mef.theme.views:api_blueprint',
            'api_monitoring = rero_mef.monitoring:api_blueprint',
            'api_agents_mef = rero_mef.agents.mef.views:api_blueprint',
            'api_agents_viaf = rero_mef.agents.viaf.views:api_blueprint',
            'api_agents_gnd = rero_mef.agents.gnd.views:api_blueprint',
            'api_agents_idref = rero_mef.agents.idref.views:api_blueprint',
            'api_agents_rero = rero_mef.agents.rero.views:api_blueprint',
        ],
        'flask.commands': [
            'fixtures = rero_mef.cli:fixtures',
            'utils = rero_mef.cli:utils',
            'celery = rero_mef.cli:celery',
            'agents = rero_mef.agents.cli:agents',
            'concepts = rero_mef.concepts.cli:concepts',
            'monitoring = rero_mef.monitoring:monitoring',
        ],
        'dojson.cli.rule': [
            'tomarc = dojson.contrib.to_marc21:to_marc21',
            'idrefjson = rero_ebooks.dojson.from_unimarc.model:from_unimarc',
        ],
        'dojson.cli.dump': [
            'pjson = rero_mef.dojson.utils:dump',
        ]
    },
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPL License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Development Status :: 3 - Alpha',
    ],
)
