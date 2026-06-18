# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Signals connector for Places."""

from rero_mef.places import PlaceGndSearch, PlaceIdrefSearch
from rero_mef.utils import make_identifier


def enrich_place_data(
    sender,
    json=None,
    record=None,
    index=None,
    doc_type=None,
    arguments=None,
    **dummy_kwargs,
):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    index_name = index.split("-")[0]
    if index_name in {PlaceGndSearch.Meta.index, PlaceIdrefSearch.Meta.index}:
        for identified_by in json.get("identifiedBy", []):
            identified_by["_identifier"] = make_identifier(identified_by)
        for match_type in {"closeMatch", "exactMatch"}:
            for match in json.get(match_type, []):
                for identified_by in match.get("identifiedBy", []):
                    identified_by["_identifier"] = make_identifier(identified_by)

        if not json.get("deleted") and (
            association_identifier := record.association_identifier
        ):
            json["_association_identifier"] = association_identifier
