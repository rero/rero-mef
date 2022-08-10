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

"""Concepts IdRef."""

import json

import click
import yaml
from flask import current_app
from invenio_db import db
from invenio_oaiharvester.models import OAIHarvestConfig
from invenio_search import current_search, current_search_client

from rero_mef.concepts import ConceptMefRecord, ConceptReroRecord
from rero_mef.utils import add_oai_source

# revision identifiers, used by Alembic.
revision = 'cd6a0e0a2a8b'
down_revision = 'c658fa8e9fa5'
branch_labels = ()
depends_on = None

INDEX_CIDREF = 'concepts_idref-idref-concept-v0.0.1-20220825'


def reindex_concepts():
    """Reindex Concepts RERO and MEF."""
    for concept in [ConceptReroRecord, ConceptMefRecord]:
        for idx, rec in enumerate(concept.get_all_records(), 1):
            click.echo(
                f'{idx:<10} Reindex Concept {concept.__name__} {rec.pid}')
            rec.reindex()


def delete_oai_harvest_config(sources):
    """Delete OAI harvest configs."""
    with current_app.app_context():
        for source_name in sources:
            if source := OAIHarvestConfig \
                    .query.filter_by(name=source_name).first():
                db.session.delete(source)
                db.session.commit()
                click.echo(f'Delete OAIHarvestConfig: {source_name}')


def init_oai_harvest_config():
    """Init OAIHarvestConfig."""
    configs = yaml.load(open('./data/oaisources.yml'), Loader=yaml.FullLoader)
    for name, values in sorted(configs.items()):
        baseurl = values['baseurl']
        metadataprefix = values.get('metadataprefix', 'marc21')
        setspecs = values.get('setspecs', '')
        comment = values.get('comment', '')
        click.echo(
            f'Add OAIHarvestConfig: {name} {baseurl} ', nl=False
        )
        msg = add_oai_source(
            name=name,
            baseurl=baseurl,
            metadataprefix=metadataprefix,
            setspecs=setspecs,
            comment=comment,
            update=True
        )
        click.echo(msg)


def update_mapping():
    """Update the mapping of a given alias."""
    for alias in current_search.aliases.keys():
        for index, f_mapping in iter(
            current_search.aliases.get(alias).items()
        ):
            mapping = json.load(open(f_mapping))
            try:
                res = current_search_client.indices.put_mapping(
                    body=mapping.get('mappings'), index=index)
            except Exception as excep:
                click.secho(
                    f'error: {excep}', fg='red')
            if res.get('acknowledged'):
                click.secho(
                    f'index: {index} has been sucessfully updated',
                    fg='green')
            else:
                click.secho(
                    f'error: {res}', fg='red')


def upgrade():
    """Upgrade database."""
    f_mapping = list(
        current_search.aliases.get('concepts_idref').values()).pop()
    mapping = json.load(open(f'{f_mapping}'))
    current_search_client.indices.create(INDEX_CIDREF, mapping)
    current_search_client.indices.put_alias(
        INDEX_CIDREF, 'concepts_idref-idref-concept-v0.0.1')
    current_search_client.indices.put_alias(
        INDEX_CIDREF, 'concepts_idref')
    click.secho(f'Index {INDEX_CIDREF} has been created.', fg='green')
    update_mapping()
    reindex_concepts()
    delete_oai_harvest_config(['idref', 'gnd'])
    init_oai_harvest_config()


def downgrade():
    """Downgrade database."""
    result = current_search_client.indices.delete(
        index=INDEX_CIDREF,
        ignore=[400, 404]
    )
    click.secho(
        f'Index {INDEX_CIDREF} has been deleted. {json.dumps(result)}',
        fg='yellow'
    )
    update_mapping()
    reindex_concepts()
    delete_oai_harvest_config(['agents.idref', 'agents.gnd', 'concepts.idref'])
    init_oai_harvest_config()
