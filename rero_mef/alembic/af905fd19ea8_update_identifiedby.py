#
# This file is part of Invenio.
# Copyright (C) 2024 RERO.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Update identifiedBy."""

from logging import getLogger

from rero_mef.concepts import ConceptIdrefRecord, ConceptIdrefSearch
from rero_mef.places import PlaceIdrefRecord, PlaceIdrefSearch
from rero_mef.utils import progressbar

# revision identifiers, used by Alembic.
revision = "af905fd19ea8"
down_revision = "28982ef7ce63"
branch_labels = ()
depends_on = None

LOGGER = getLogger("alembic")


def upgrade():
    """Upgrade database.

    Update identifiedBy in closeMatch to list.
    """
    for record_type in [
        {"search_cls": ConceptIdrefSearch, "record_cls": ConceptIdrefRecord},
        {"search_cls": PlaceIdrefSearch, "record_cls": PlaceIdrefRecord},
    ]:
        query = record_type["search_cls"]().filter(
            "exists", field="closeMatch.identifiedBy"
        )
        pids = [hit.pid for hit in query.source("pid").scan()]
        name = record_type["search_cls"].Meta.index
        LOGGER.info(f"Change closeMatch.identifiedBy to list {name}: {len(pids)}")
        progress_bar = progressbar(
            items=pids,
            length=len(pids),
            verbose=True,
        )
        for pid in progress_bar:
            if record := record_type["record_cls"].get_record_by_pid(pid):
                new_close_matchs = []
                for close_match in record.get("closeMatch", []):
                    new_close_matchs.append(close_match)
                    if (
                        ifidentified_by := close_match.get("identifiedBy")
                    ) and not isinstance(ifidentified_by, list):
                        new_close_matchs[-1]["identifiedBy"] = [ifidentified_by]
                record["closeMatch"] = new_close_matchs
                record.update(data=record, dbcommit=True, reindex=True)

        query = record_type["search_cls"]().filter("exists", field="identifiedBy")
        identified_by_pids = [
            hit.pid for hit in query.source("pid").scan() if hit.pid not in pids
        ]
        LOGGER.info(f"Reindex identifiedBy {name}: {len(identified_by_pids)}")
        progress_bar = progressbar(
            items=identified_by_pids,
            length=len(identified_by_pids),
            verbose=True,
        )
        for pid in progress_bar:
            if record := record_type["record_cls"].get_record_by_pid(pid):
                record.reindex()


def downgrade():
    """Downgrade database.

    Update identifiedBy in closeMatch to object.
    """
    for record_type in [
        {"search_cls": ConceptIdrefSearch, "record_cls": ConceptIdrefRecord},
        {"search_cls": PlaceIdrefSearch, "record_cls": PlaceIdrefRecord},
    ]:
        query = record_type["search_cls"]().filter(
            "exists", field="closeMatch.identifiedBy"
        )
        pids = [hit.pid for hit in query.source("pid").scan()]
        name = record_type["search_cls"].Meta.index
        LOGGER.info(f"Change identifiedBy to object {name}: {query.count()}")

        progress_bar = progressbar(
            items=pids,
            length=query.count(),
            verbose=True,
        )
        for pid in progress_bar:
            if record := record_type["record_cls"].get_record_by_pid(pid):
                new_close_matchs = []
                for close_match in record.get("closeMatch", []):
                    new_close_matchs.append(close_match)
                    if (
                        ifidentified_by := close_match.get("identifiedBy")
                    ) and isinstance(ifidentified_by, list):
                        new_close_matchs[-1]["identifiedBy"] = ifidentified_by[0]
                record["closeMatch"] = new_close_matchs
                record.update(data=record, dbcommit=True, reindex=True)
