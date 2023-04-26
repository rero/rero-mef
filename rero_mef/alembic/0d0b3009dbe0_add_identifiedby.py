#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add identifiedBy."""

import click

from rero_mef.utils import get_entity_class, progressbar

# revision identifiers, used by Alembic.
revision = '0d0b3009dbe0'
down_revision = 'cd6a0e0a2a8b'
branch_labels = ()
depends_on = None

agents = {
    'aggnd': 'GND',
    'aidref': 'IdRef',
    'agrero': 'RERO'
}


def upgrade():
    """Upgrade database."""
    for agent, name in agents.items():
        agent_class = get_entity_class(agent.lower())
        click.echo(f'Add identifiedBy to {agent}')
        progress_bar = progressbar(
            items=agent_class.get_all_records(),
            length=agent_class.count(),
            verbose=True
        )
        for rec in progress_bar:
            has_not_identified_by_uri = True
            if identifier := rec.get('identifier'):
                for identified_by in rec.get('identifiedBy', []):
                    if identified_by['value'] == identifier:
                        has_not_identified_by_uri = False
                if has_not_identified_by_uri:
                    rec.setdefault('identifiedBy', []).append({
                        'type': 'uri',
                        'value': identifier,
                        'source': name
                    })
                    rec.update(data=rec, dbcommit=True, reindex=True)


def downgrade():
    """Downgrade database."""
    for agent, name in agents.items():
        agent_class = get_entity_class(agent.lower())
        click.echo(f'Remove identifiedBy to {agent}')
        progress_bar = progressbar(
            items=agent_class.get_all_records(),
            length=agent_class.count(),
            verbose=True
        )
        for rec in progress_bar:
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