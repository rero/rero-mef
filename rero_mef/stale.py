# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Find and repair MEF records whose association the rules no longer support.

A record's association depends on the other records claiming the same
identifier, but a harvest only reprocesses the record that changed. When a
second record starts claiming an identifier, the newcomer is reprocessed and
correctly gets no partner, while the pair that already existed is never looked
at again -- so a link the rules refuse stays stored. `Holzwerkstoff` started
claiming the BNF number of `Bois` months after `Holz` had been linked to it,
and nothing told that MEF record.

The audit reads the search index only: three scans build the same picture
`get_association_record` would, and the winner is decided by the rules
themselves rather than a copy of them, so it cannot drift. Only the records
whose stored partner disagrees are reprocessed.
"""

import collections

from flask import current_app

from .utils import get_entity_class, get_entity_search_class

#: Entity families to audit, as (side that owns the decision, other side, MEF class name).
ASSOCIATION_PAIRS = (
    ("cidref", "cognd", "comef"),
    ("pidref", "plgnd", "plmef"),
)


def _association_index(record_type):
    """Read every association identifier of a source from the index.

    :param record_type: Entity record type.
    :returns: Tuple (identifier -> [(pid, level)], pid -> identifiers).
    """
    by_identifier = collections.defaultdict(list)
    by_pid = {}
    hits = (
        get_entity_search_class(record_type)()
        .filter("exists", field="_association_identifier")
        .source(["pid", "_association_identifier", "_association_level"])
        .scan()
    )
    for hit in hits:
        data = hit.to_dict()
        identifiers = data.get("_association_identifier") or []
        if isinstance(identifiers, str):
            identifiers = [identifiers]
        by_pid[data["pid"]] = identifiers
        for identifier in identifiers:
            by_identifier[identifier].append((data["pid"], data.get("_association_level")))
    return by_identifier, by_pid


def _expected_partner(record_cls, pid, identifiers, own_index, other_index):
    """Get the partner the rules give a record, from the indexed identifiers.

    :param record_cls: Record class of the side that owns the decision.
    :param pid: Pid of that record.
    :param identifiers: Its association identifiers.
    :param own_index: Identifier -> claimants on its own side.
    :param other_index: Identifier -> claimants on the other side.
    :returns: Pid of the partner, or None when the rules give none.
    """
    if not identifiers:
        return None
    own = {claim: level for identifier in identifiers for claim, level in own_index.get(identifier, [])}
    if len(own) > 1 and record_cls._single_association_pid(list(own.items())) != pid:
        return None
    other = {claim: level for identifier in identifiers for claim, level in other_index.get(identifier, [])}
    return record_cls._single_association_pid(list(other.items())) if other else None


def _stored_partners(mef_type, own_name, other_name):
    """Read the pairs a MEF index holds.

    :param mef_type: MEF record type.
    :param own_name: Name of the side that owns the decision.
    :param other_name: Name of the other side.
    :returns: Dict own pid -> (mef pid, other pid).
    """
    hits = (
        get_entity_search_class(mef_type)()
        .filter("exists", field=own_name)
        .filter("exists", field=other_name)
        .source(["pid", f"{own_name}.pid", f"{other_name}.pid"])
        .scan()
    )
    stored = {}
    for hit in hits:
        data = hit.to_dict()
        own, other = data.get(own_name) or {}, data.get(other_name) or {}
        if own.get("pid") and other.get("pid"):
            stored[own["pid"]] = (data["pid"], other["pid"])
    return stored


def audit(own_type, other_type, mef_type):
    """Compare the pairs a MEF index holds with the pairs the rules give.

    :param own_type: Record type of the side that owns the decision.
    :param other_type: Record type of the other side.
    :param mef_type: MEF record type.
    :returns: List of (own pid, mef pid, stored partner, expected partner).
    """
    record_cls = get_entity_class(own_type)
    own_index, own_identifiers = _association_index(own_type)
    other_index, _ = _association_index(other_type)
    stored = _stored_partners(mef_type, record_cls.name, get_entity_class(other_type).name)

    divergent = []
    for pid, (mef_pid, partner) in stored.items():
        expected = _expected_partner(record_cls, pid, own_identifiers.get(pid, []), own_index, other_index)
        if expected != partner:
            divergent.append((pid, mef_pid, partner, expected))
    return divergent


def repair(own_type, divergent, verbose=False):
    """Rebuild the MEF record of every record whose partner has gone stale.

    :param own_type: Record type of the side that owns the decision.
    :param divergent: Result of :func:`audit`.
    :param verbose: Echo every record.
    :returns: Number of records reprocessed.
    """
    record_cls = get_entity_class(own_type)
    repaired = 0
    for pid, mef_pid, partner, expected in divergent:
        record = record_cls.get_record_by_pid(pid)
        if not record:
            continue
        record.create_or_update_mef(dbcommit=True, reindex=True)
        repaired += 1
        if verbose:
            current_app.logger.info(
                f"STALE ASSOCIATION REPAIRED: {own_type} {pid} | mef {mef_pid} | {partner} -> {expected}"
            )
    if repaired:
        record_cls.flush_indexes()
    return repaired
