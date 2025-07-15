#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""delete identifier."""

from invenio_db import db

from rero_mef.agents import (
    AgentGndIndexer,
    AgentGndRecord,
    AgentIdrefIndexer,
    AgentIdrefRecord,
    AgentReroIndexer,
    AgentReroRecord,
)
from rero_mef.utils import progressbar

# revision identifiers, used by Alembic.
revision = "d8536341fc5e"
down_revision = "af905fd19ea8"
branch_labels = ()
depends_on = None

agents = [
    {
        "record_cls": AgentGndRecord,
        "index_cls": AgentGndIndexer,
        "url": "http://d-nb.info/gnd/",
    },
    {
        "record_cls": AgentIdrefRecord,
        "index_cls": AgentIdrefIndexer,
        "url": "http://www.idref.fr",
    },
    {
        "record_cls": AgentReroRecord,
        "index_cls": AgentReroIndexer,
        "url": "http://data.rero.ch/02-",
    },
]


def upgrade():
    """Upgrade database."""
    for agent in agents:
        agent_cls = agent["record_cls"]
        indexer = agent["index_cls"]()
        query = agent_cls.search().filter("exists", field="identifier")
        progress_bar = progressbar(
            items=query.source().scan(),
            length=query.count(),
            label=agent_cls.name,
            verbose=True,
        )
        ids = []
        for idx, hit in enumerate(progress_bar, 1):
            id_ = hit.meta.id
            ids.append(id_)
            rec = agent_cls.get_record(id_)
            rec.pop("identifier", None)
            rec.update(data=rec, dbcommit=False, reindex=True)
            if idx % 1000 == 0:
                db.session.commit()
                indexer.bulk_index(ids)
                indexer.process_bulk_queue()
                ids = []
        db.session.commit()
        indexer.bulk_index(ids)
        indexer.process_bulk_queue()


def downgrade():
    """Downgrade database."""
    for agent in agents:
        agent_cls = agent["record_cls"]
        indexer = agent["index_cls"]()
        url = agent["url"]
        query = agent_cls.search().exclude("exists", field="identifier")
        progress_bar = progressbar(
            items=query.source().scan(),
            length=query.count(),
            label=agent_cls.name,
            verbose=True,
        )
        ids = []
        for idx, hit in enumerate(progress_bar, 1):
            id_ = hit.meta.id
            ids.append(id_)
            rec = agent_cls.get_record(id_)
            rec["identifier"] = f'"{url}{rec.pid}"'
            rec.update(data=rec, dbcommit=False, reindex=True)
            if idx % 1000 == 0:
                db.session.commit()
                indexer.bulk_index(ids)
                indexer.process_bulk_queue()
                ids = []
        db.session.commit()
        indexer.bulk_index(ids)
        indexer.process_bulk_queue()
