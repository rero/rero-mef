#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add identifiedBy."""

from copy import deepcopy

import click
from invenio_db import db

from rero_mef.agents import AgentMefIndexer, AgentMefRecord
from rero_mef.utils import get_entity_class, get_entity_indexer_class, progressbar

# revision identifiers, used by Alembic.
revision = "0d0b3009dbe0"
down_revision = "cd6a0e0a2a8b"
branch_labels = ()
depends_on = None

COMMIT_COUNT = 1000

agents = {"aggnd": "GND", "aidref": "IDREF", "agrero": "RERO"}


def change_identified_by_source(identifiers, old_source, new_source):
    """Change identifiedBy['source']."""
    if identifiers:
        for identified_by in identifiers:
            if identified_by.get("source") == old_source:
                identified_by["source"] = new_source


def has_identified_by_uri(identifiers, identifier, name):
    """Has identified by uri."""
    for identified_by in identifiers:
        if identified_by.get("source") == name and identified_by["value"] == identifier:
            return True
    return False


def upgrade():
    """Upgrade database."""
    for agent, name in agents.items():
        agent_class = get_entity_class(agent)
        indexer = get_entity_indexer_class(agent)()
        click.echo(f"Add identifiedBy and type to {agent}: {agent_class.count()}")
        progress_bar = progressbar(
            items=agent_class.get_all_records(),
            length=agent_class.count(),
            verbose=True,
        )
        ids = []
        for idx, rec in enumerate(progress_bar, 1):
            change_identified_by_source(
                identifiers=rec.get("identifiedBy"),
                old_source="IdRef",
                new_source="IDREF",
            )
            if identifier := rec.get("identifier"):
                if not has_identified_by_uri(
                    rec.get("identifiedBy", []), identifier, name
                ):
                    rec.setdefault("identifiedBy", []).append(
                        {"type": "uri", "value": identifier, "source": name}
                    )
            rec["type"] = rec["bf:Agent"]
            ids.append(rec.id)
            rec.update(data=rec, dbcommit=False, reindex=False)
            if idx % COMMIT_COUNT == 0:
                db.session.commit()
                indexer.bulk_index(ids)
                indexer.process_bulk_queue()
                ids = []
        db.session.commit()
        indexer.bulk_index(ids)
        indexer.process_bulk_queue()

    click.echo(f"Add type to mef: {AgentMefRecord.count()}")
    progress_bar = progressbar(
        items=AgentMefRecord.get_all_records(),
        length=AgentMefRecord.count(),
        verbose=True,
    )
    ids = []
    indexer = AgentMefIndexer()
    for idx, rec in enumerate(progress_bar, 1):
        replace_refs_data = deepcopy(rec).replace_refs()
        for agent in rec.entities:
            if agent in replace_refs_data:
                rec["type"] = replace_refs_data[agent]["bf:Agent"]
                break
        ids.append(rec.id)
        rec.update(data=rec, dbcommit=False, reindex=False)
        if idx % COMMIT_COUNT == 0:
            db.session.commit()
            indexer.bulk_index(ids)
            indexer.process_bulk_queue()
            ids = []
    db.session.commit()
    indexer.bulk_index(ids)
    indexer.process_bulk_queue()

    for concept in ["cidref", "corero", "comef"]:
        concept_class = get_entity_class(concept)
        indexer = get_entity_indexer_class(concept)()
        click.echo(f"Add type to {concept_class.name}: {concept_class.count()}")
        progress_bar = progressbar(
            items=concept_class.get_all_records(),
            length=concept_class.count(),
            verbose=True,
        )
        ids = []
        for idx, rec in enumerate(progress_bar, 1):
            rec["type"] = "bf:Concept"
            change_identified_by_source(
                identifiers=rec.get("identifiedBy"),
                old_source="IdRef",
                new_source="IDREF",
            )
            ids.append(rec.id)
            rec.update(data=rec, dbcommit=False, reindex=False)
            if idx % COMMIT_COUNT == 0:
                db.session.commit()
                indexer.bulk_index(ids)
                indexer.process_bulk_queue()
                ids = []
        db.session.commit()
        indexer.bulk_index(ids)
        indexer.process_bulk_queue()


def downgrade():
    """Downgrade database."""
    for agent, _ in agents.items():
        agent_class = get_entity_class(agent.lower())
        click.echo(f"Remove identifiedBy from {agent}: {agent_class.count()}")
        progress_bar = progressbar(
            items=agent_class.get_all_records(),
            length=agent_class.count(),
            verbose=True,
        )
        for idx, rec in enumerate(progress_bar, 1):
            change_identified_by_source(
                identifiers=rec.get("identifiedBy"),
                old_source="IDREF",
                new_source="IdRef",
            )
            if identifier := rec.get("identifier"):
                if new_identified_by := [
                    identified_by
                    for identified_by in rec.get("identifiedBy", [])
                    if identified_by["value"] != identifier
                ]:
                    rec["identifiedBy"] = new_identified_by
                    rec.update(data=rec, dbcommit=False, reindex=True)
                elif rec.pop("identifiedBy", None):
                    rec.update(data=rec, dbcommit=False, reindex=True)
            if idx % COMMIT_COUNT == 0:
                db.session.commit()
        db.session.commit()

    click.echo(f"Remove type to mef: {AgentMefRecord.count()}")
    progress_bar = progressbar(
        items=AgentMefRecord.get_all_records(),
        length=AgentMefRecord.count(),
        verbose=True,
    )
    for idx, rec in enumerate(progress_bar, 1):
        if rec.pop("type"):
            rec.update(data=rec, dbcommit=False, reindex=True)
        if idx % COMMIT_COUNT == 0:
            db.session.commit()
    db.session.commit()

    for concept in ["cidref", "corero", "comef"]:
        concept_class = get_entity_class(concept)
        click.echo(f"Remove type from {concept_class.name}: {concept_class.count()}")
        progress_bar = progressbar(
            items=concept_class.get_all_records(),
            length=concept_class.count(),
            verbose=True,
        )
        for idx, rec in enumerate(progress_bar, 1):
            if rec.pop("type"):
                change_identified_by_source(
                    identifiers=rec.get("identifiedBy"),
                    old_source="IDREF",
                    new_source="IdRef",
                )
                rec.update(data=rec, dbcommit=False, reindex=True)
            if idx % COMMIT_COUNT == 0:
                db.session.commit()
        db.session.commit()
