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

"""
MEF (Multilingual Entity File) server with records for persons, works, etc.
for reuse in integrated library systems (ILS).
"""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()

INVENIO_VERSION = "3.2.1"

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
            'idref = rero_mef.agents.idref.tasks'
            'gnd = rero_mef.agents.gnd.tasks'
        ],
        'console_scripts': [
            'rero-mef = invenio_app.cli:cli',
        ],
        'invenio_assets.webpack': [
            'rero_mef_css = rero_mef.theme.webpack:theme',
        ],
        'invenio_base.apps': [
            'rero-mef = rero_mef.ext:REROMEFAPP'
        ],
        'invenio_base.blueprints': [
            'rero_mef = rero_mef.theme.views:blueprint',
        ],
        'invenio_base.api_blueprints': [
            'api_rero_mef = rero_mef.theme.views:api_blueprint',
            'monitoring = rero_mef.monitoring:api_blueprint',
        ],
        'invenio_config.module': [
            'rero_mef = rero_mef.config',
        ],
        'invenio_db.models': [
            'mef = rero_mef.mef.models',
            'viaf = rero_mef.viaf.models',
            'agents_gnd = rero_mef.agents.gnd.models',
            'agents_idref = rero_mef.agents.idref.models',
            'agents_rero = rero_mef.agents.rero.models',
            'concepts_rero = rero_mef.concepts.rero.models',
        ],
        'invenio_pidstore.minters': [
            'mef_id = rero_mef.mef.minters:mef_id_minter',
            'viaf_id = rero_mef.viaf.minters:viaf_id_minter',
            'agent_gnd_id = rero_mef.agents.gnd.minters:gnd_id_minter',
            'agent_idref_id = rero_mef.agents.idref.minters:idref_id_minter',
            'agent_rero_id = rero_mef.agents.rero.minters:rero_id_minter',
            'concept_rero_id = rero_mef.concepts.rero.minters:rero_id_minter'
        ],
        'invenio_pidstore.fetchers': [
            'mef_id = rero_mef.mef.fetchers:mef_id_fetcher',
            'viaf_id = rero_mef.viaf.fetchers:viaf_id_fetcher',
            'agent_gnd_id = rero_mef.agents.gnd.fetchers:gnd_id_fetcher',
            'agent_idref_id = rero_mef.agents.idref.fetchers:idref_id_fetcher',
            'agent_rero_id = rero_mef.agents.rero.fetchers:rero_id_fetcher',
            'concept_rero_id = rero_mef.concepts.rero.fetchers:rero_id_fetcher',
        ],
        'invenio_jsonschemas.schemas': [
            'common = rero_mef.jsonschemas',
            'mef = rero_mef.mef.jsonschemas',
            'viaf = rero_mef.viaf.jsonschemas',
            'agents_gnd = rero_mef.agents.gnd.jsonschemas',
            'agents_idref = rero_mef.agents.idref.jsonschemas',
            'agents_rero = rero_mef.agents.rero.jsonschemas',
            'cocepts_rero = rero_mef.concepts.rero.jsonschemas'
        ],
        'invenio_search.mappings': [
            'mef = rero_mef.mef.mappings',
            'viaf = rero_mef.viaf.mappings',
            'agents_gnd = rero_mef.agents.gnd.mappings',
            'agents_idref = rero_mef.agents.idref.mappings',
            'agents_rero = rero_mef.agents.rero.mappings',
            'concepts_rero = rero_mef.concepts.rero.mappings'
        ],
        'invenio_records.jsonresolver': [
            'mef = rero_mef.mef.jsonresolvers.mef_resolver',
            'agents_gnd = rero_mef.agents.gnd.jsonresolvers.gnd_resolver',
            'agents_idref = rero_mef.agents.idref.jsonresolvers.idref_resolver',
            'agents_rero = rero_mef.agents.rero.jsonresolvers.rero_resolver',
            'concepts_rero = rero_mef.concepts.rero.jsonresolvers.rero_resolver',
        ],
        'flask.commands': [
            'fixtures = rero_mef.cli:fixtures',
            'utils = rero_mef.cli:utils',
            'celery = rero_mef.cli:celery',
        ],
        'dojson.cli.rule': [
            'tomarc = dojson.contrib.to_marc21:to_marc21',
            'idrefjson = rero_ebooks.dojson.from_unimarc.model:from_unimarc'
        ],
        'dojson.cli.dump': [
            'pjson = rero_mef.dojson.utils:dump'
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
        'Programming Language :: Python :: 3.6',
        'Development Status :: 3 - Alpha',
    ],
)
