#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""delete bf:Agent."""

from logging import getLogger

from invenio_db import db
from sqlalchemy import func

from rero_mef.utils import get_entity_class

# revision identifiers, used by Alembic.
revision = '28982ef7ce63'
down_revision = '0d0b3009dbe0'
branch_labels = ()
depends_on = None

LOGGER = getLogger('alembic')

agents = {
    'aggnd': 'GND',
    'aidref': 'IDREF',
    'agrero': 'RERO'
}


def commit_changes(indexer, ids):
    """Commit changes and reindex."""
    db.session.commit()
    indexer.bulk_index(ids)
    indexer.process_bulk_queue()


def upgrade():
    """Upgrade database.

    Delete all remaining bf:Agents from agents in database.
    """
    for agent, name in agents.items():
        agent_class = get_entity_class(agent)

        count = agent_class.model_cls.query.filter(
            agent_class.model_cls.json.op('->')('bf:Agent') is not None
        ).update(
            {
                agent_class.model_cls.json:
                agent_class.model_cls.json - "bf:Agent"
            },
            synchronize_session=False
        )
        LOGGER.info(f'Delete bf:Agent from {agent}: {count}')
        db.session.commit()
    # For ES: update mapping must be done.


def downgrade():
    """Downgrade database.

    Adds bf:Agents to agents in database.
    """
    for agent, name in agents.items():
        agent_class = get_entity_class(agent)

        count = agent_class.model_cls.query.filter(
            agent_class.model_cls.json.op('->')('type') is not None
        ).update(
            {
                "json": func.jsonb_set(
                    agent_class.model_cls.json,
                    '{bf:Agent}',
                    agent_class.model_cls.json.op('->')('type')
                )
            },
            synchronize_session=False
        )
        LOGGER.info(f'Add bf:Agent to {agent}: {count}')
        db.session.commit()
    # For ES: update mapping must be done
    # and all agents and MEF have to be reindexed
