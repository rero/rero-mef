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
            'contributions = rero_mef.contributions.tasks',
            'idref = rero_mef.contributions.idref.tasks'
            'gnd = rero_mef.contributions.gnd.tasks'
        ],
        'console_scripts': [
            'rero-mef = invenio_app.cli:cli',
        ],
        'invenio_assets.bundles': [
            'rero_mef_css = rero_mef.bundles:mef_css',
        ],
        'invenio_base.apps': [
            'rero-mef = rero_mef.ext:REROMEFAPP'
        ],
        'invenio_base.blueprints': [
            'rero_mef = rero_mef.views:blueprint',
        ],
        'invenio_base.api_blueprints': [
            'api_rero_mef = rero_mef.views:api_blueprint'
        ],
        'invenio_config.module': [
            'rero_mef = rero_mef.config',
        ],
        'invenio_db.models': [
            'viaf = rero_mef.contributions.viaf.models',
            'gnd = rero_mef.contributions.gnd.models',
            'rero = rero_mef.contributions.rero.models',
            'mef = rero_mef.contributions.mef.models',
            'idref = rero_mef.contributions.idref.models'
            'agencies = rero_mef.contributions.models'
        ],
        'invenio_pidstore.minters': [
            'viaf = rero_mef.contributions.viaf.minters:viaf_id_minter',
            'gnd = rero_mef.contributions.gnd.minters:gnd_id_minter',
            'rero = rero_mef.contributions.rero.minters:rero_id_minter',
            'mef = rero_mef.contributions.mef.minters:mef_id_minter',
            'idref = rero_mef.contributions.idref.minters:idref_id_minter'

        ],
        'invenio_pidstore.fetchers': [
            'viaf = rero_mef.contributions.viaf.fetchers:viaf_id_fetcher',
            'gnd = rero_mef.contributions.gnd.fetchers:gnd_id_fetcher',
            'rero = rero_mef.contributions.rero.fetchers:rero_id_fetcher',
            'mef = rero_mef.contributions.mef.fetchers:mef_id_fetcher',
            'idref = rero_mef.contributions.idref.fetchers:idref_id_fetcher'
        ],
        'invenio_jsonschemas.schemas': [
            'common = rero_mef.jsonschemas',
            'viaf = rero_mef.contributions.viaf.jsonschemas',
            'gnd = rero_mef.contributions.gnd.jsonschemas',
            'rero = rero_mef.contributions.rero.jsonschemas',
            'mef = rero_mef.contributions.mef.jsonschemas',
            'idref = rero_mef.contributions.idref.jsonschemas'
        ],
        'invenio_search.mappings': [
            'viaf = rero_mef.contributions.viaf.mappings',
            'gnd = rero_mef.contributions.gnd.mappings',
            'rero = rero_mef.contributions.rero.mappings',
            'mef = rero_mef.contributions.mef.mappings',
            'idref = rero_mef.contributions.idref.mappings'
        ],
        'invenio_records.jsonresolver': [
            'gnd = rero_mef.contributions.gnd.jsonresolvers.gnd_resolver',
            'rero = rero_mef.contributions.rero.jsonresolvers.rero_resolver',
            'mef = rero_mef.contributions.mef.jsonresolvers.mef_resolver',
            'idref = rero_mef.contributions.idref.jsonresolvers.idref_resolver'
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
        ],
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
