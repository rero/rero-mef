#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add identifiedBy."""

from copy import deepcopy

import click

from rero_mef.agents import AgentMefRecord
from rero_mef.utils import get_entity_class, progressbar

# revision identifiers, used by Alembic.
revision = '0d0b3009dbe0'
down_revision = 'cd6a0e0a2a8b'
branch_labels = ()
depends_on = None

agents = {
    'aggnd': 'GND',
    'aidref': 'IDREF',
    'agrero': 'RERO'
}


def chnage_identified_by_source(identifiers, old_source, new_source):
    """Change identifiedBy['source']."""
    if identifiers:
        for identified_by in identifiers:
            if identified_by.get('source') == old_source:
                identified_by['source'] = new_source


def upgrade():
    """Upgrade database."""
    for agent, name in agents.items():
        agent_class = get_entity_class(agent)
        click.echo(
            f'Add identifiedBy and type to {agent}: {agent_class.count()}')
        progress_bar = progressbar(
            items=agent_class.get_all_records(),
            length=agent_class.count(),
            verbose=True
        )
        for rec in progress_bar:
            chnage_identified_by_source(
                identifiers=rec.get('identifiedBy'),
                old_source='IdRef',
                new_source='IDREF'
            )
            has_not_identified_by_uri = True
            if identifier := rec.get('identifier'):
                if has_not_identified_by_uri:
                    rec.setdefault('identifiedBy', []).append({
                        'type': 'uri',
                        'value': identifier,
                        'source': name
                    })
            rec['type'] = rec['bf:Agent']
            rec.update(data=rec, dbcommit=True, reindex=True)

    click.echo(f'Add type to mef: {AgentMefRecord.count()}')
    progress_bar = progressbar(
        items=AgentMefRecord.get_all_records(),
        length=AgentMefRecord.count(),
        verbose=True
    )
    for rec in progress_bar:
        replace_refs_data = deepcopy(rec).replace_refs()
        for agent in rec.entities:
            if agent in replace_refs_data:
                rec['type'] = replace_refs_data[agent]['bf:Agent']
                break
        rec.update(data=rec, dbcommit=True, reindex=True)

    for concept in ['cidref', 'corero', 'comef']:
        concept_class = get_entity_class(concept)
        click.echo(
            f'Add type to {concept_class.name}: {concept_class.count()}')
        progress_bar = progressbar(
            items=concept_class.get_all_records(),
            length=concept_class.count(),
            verbose=True
        )
        for rec in progress_bar:
            rec['type'] = 'bf:Concept'
            chnage_identified_by_source(
                identifiers=rec.get('identifiedBy'),
                old_source='IdRef',
                new_source='IDREF'
            )
            rec.update(data=rec, dbcommit=True, reindex=True)


def downgrade():
    """Downgrade database."""
    for agent, _ in agents.items():
        agent_class = get_entity_class(agent.lower())
        click.echo(f'Remove identifiedBy from {agent}: {agent_class.count()}')
        progress_bar = progressbar(
            items=agent_class.get_all_records(),
            length=agent_class.count(),
            verbose=True
        )
        for rec in progress_bar:
            chnage_identified_by_source(
                identifiers=rec.get('identifiedBy'),
                old_source='IDREF',
                new_source='IdRef'
            )
            if identifier := rec.get('identifier'):
                if new_identified_by := [
                    identified_by
                    for identified_by in rec.get('identifiedBy', [])
                    if identified_by['value'] != identifier
                ]:
                    rec['identifiedBy'] = new_identified_by
                    rec.update(data=rec, dbcommit=True, reindex=True)
                elif rec.pop('identifiedBy', None):
                    rec.update(data=rec, dbcommit=True, reindex=True)

    click.echo(f'Remove type to mef: {AgentMefRecord.count()}')
    progress_bar = progressbar(
        items=AgentMefRecord.get_all_records(),
        length=AgentMefRecord.count(),
        verbose=True
    )
    for rec in progress_bar:
        if rec.pop('type'):
            rec.update(data=rec, dbcommit=True, reindex=True)

    for concept in ['cidref', 'corero', 'comef']:
        concept_class = get_entity_class(concept)
        click.echo(
            f'Remove type from {concept_class.name}: {concept_class.count()}')
        progress_bar = progressbar(
            items=concept_class.get_all_records(),
            length=concept_class.count(),
            verbose=True
        )
        for rec in progress_bar:
            if rec.pop('type'):
                chnage_identified_by_source(
                    identifiers=rec.get('identifiedBy'),
                    old_source='IDREF',
                    new_source='IdRef'
                )
                rec.update(data=rec, dbcommit=True, reindex=True)
