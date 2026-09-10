# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Utilities."""

import re
from copy import deepcopy

from flask import current_app
from invenio_records_rest.utils import obj_or_import_string

BNF_NUMBER = re.compile(r"^FRBNF(\d{8})|^https?://[\w.]+\.bnf\.fr/ark:/12148/cb(\d{8})")

#: GND match types, strongest first: `exactMatch` asserts equivalence, `closeMatch` only relatedness.
MATCH_TYPES = ("exactMatch", "closeMatch")


def bnf_association_identifier(value):
    """Get the canonical BNF association identifier of an identifier value.

    BNF numbers are written in incompatible ways: IdRef stores `FRBNF` plus
    eight digits, GND sometimes keeps the trailing check character, and both
    store the same number again as a BNF ark uri. Only the eight digits are
    stable, so they are the association identifier.

    :param value: Identifier value.
    :returns: `FRBNF` plus the eight digits, or None.
    """
    if match := BNF_NUMBER.match(value or ""):
        return f"FRBNF{match[1] or match[2]}"
    return None


def bnf_association_identifiers(identified_by_lists):
    """Get the canonical BNF association identifiers of `identifiedBy` lists.

    Only `bf:Nbn` values identify a record. The BNF ark uri repeats the same
    number on all but a few hundred records, and it is never read as an
    identifier: where the two disagree the `bf:Nbn` is taken and
    :func:`bnf_ark_disagreements` reports the ark so the source can be fixed.

    :param identified_by_lists: Iterable of `identifiedBy` lists.
    :returns: Set of association identifiers.
    """
    return {
        identifier
        for identified_by_list in identified_by_lists
        for identified_by in identified_by_list
        if identified_by.get("type") == "bf:Nbn"
        if (identifier := bnf_association_identifier(identified_by.get("value")))
    }


def _bnf_ark_identifiers(identified_by_lists):
    """Get the BNF numbers the ark uris of `identifiedBy` lists state."""
    return {
        identifier
        for identified_by_list in identified_by_lists
        for identified_by in identified_by_list
        if identified_by.get("type") != "bf:Nbn"
        if (identifier := bnf_association_identifier(identified_by.get("value")))
    }


def bnf_ark_disagreements(identified_by_lists):
    """Get the BNF numbers the ark uris state and the `bf:Nbn` values do not.

    A record whose ark and `bf:Nbn` name different BNF records contradicts
    itself, and one whose number is only in an ark cannot be associated at all.
    Both are source data errors worth reporting.

    :param identified_by_lists: Iterable of `identifiedBy` lists.
    :returns: Set of BNF numbers only the arks state.
    """
    identified_by_lists = list(identified_by_lists)
    return _bnf_ark_identifiers(identified_by_lists) - bnf_association_identifiers(identified_by_lists)


def bnf_ark_disagreements_by_match_type(record, match_types=MATCH_TYPES):
    """Get the contradicting BNF arks of every match type of a record.

    Each match type is audited on its own, whichever one the association is
    finally read from: an ark contradicting its `bf:Nbn` is a source data error
    worth reporting even in a block the selection never reaches.

    :param record: Record holding the match blocks.
    :param match_types: Match types to audit.
    :returns: Dict match type -> BNF numbers only its arks state, the agreeing
        match types left out.
    """
    disagreements = {}
    for match_type in match_types:
        if only_ark := bnf_ark_disagreements(match.get("identifiedBy", []) for match in record.get(match_type, [])):
            disagreements[match_type] = only_ark
    return disagreements


def get_concept_endpoints():
    """Get all contributions from config."""
    concepts = current_app.config.get("RERO_CONCEPTS", [])
    endpoints = current_app.config.get("RECORDS_REST_ENDPOINTS", {})
    return {endpoint: data for endpoint, data in endpoints.items() if endpoint in concepts}


def get_concept_classes(without_mef=True):
    """Get concept classes from config."""
    concepts = {}
    endpoints = deepcopy(get_concept_endpoints())
    if without_mef:
        concepts.pop("comef", None)
    for concept in endpoints:
        if record_class := obj_or_import_string(endpoints[concept].get("record_class")):
            concepts[concept] = record_class
    return concepts
