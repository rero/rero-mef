# RERO MEF
# Copyright (C) 2026 RERO
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

"""Signals connector for MEF records (agents, concepts, places)."""

from flask import current_app

from rero_mef.agents.mef.api import AgentMefSearch
from rero_mef.concepts.mef.api import ConceptMefSearch
from rero_mef.places.mef.api import PlaceMefSearch
from rero_mef.utils import get_entity_class

_MEF_INDEX_TO_ENTITY = {
    AgentMefSearch.Meta.index: "agents",
    ConceptMefSearch.Meta.index: "concepts",
    PlaceMefSearch.Meta.index: "places",
}

_MEF_INDEXES = set(_MEF_INDEX_TO_ENTITY)


def _get_entity_class_by_ref(ref_url):
    """Return the record class matching a $ref URL via list_route lookup.

    The $ref URL has the form ``https://<host>/api<list_route><pid>``, e.g.
    ``https://mef.rero.ch/api/agents/idref/EXAI004``.  Matching by the two
    trailing path segments against each endpoint's ``list_route`` is more
    reliable than guessing from the URL segment alone.

    :param ref_url: The $ref URL string.
    :returns: Record class or None.
    """
    parts = ref_url.rstrip("/").split("/")
    if len(parts) < 3:
        return None
    # Reconstruct the list_route as "/<group>/<type>/"
    route = f"/{parts[-3]}/{parts[-2]}/"
    endpoints = current_app.config.get("RECORDS_REST_ENDPOINTS", {})
    key = next(
        (k for k, cfg in endpoints.items() if cfg.get("list_route") == route), None
    )
    return get_entity_class(key) if key else None


def _find_source_type(entity_name, pid):
    """Return the bf:type of the first record found for pid across all classes sharing entity_name.

    Searches all endpoints whose route ends with ``/<entity_name>/`` (e.g. aggnd, cognd, plgnd
    for entity_name="gnd") so a redirect target in a different entity group is found.

    :param entity_name: Source entity name, e.g. ``gnd``, ``idref``, ``rero``.
    :param pid: PID to look up.
    :returns: bf:type string, or None if not found anywhere.
    """
    endpoints = current_app.config.get("RECORDS_REST_ENDPOINTS", {})
    suffix = f"/{entity_name}/"
    for key, cfg in endpoints.items():
        if not cfg.get("list_route", "").endswith(suffix):
            continue
        rec_class = get_entity_class(key)
        if rec_class is None:
            continue
        rec = rec_class.get_record_by_pid(pid)
        if rec is not None:
            return rec.get("type")
    return None


def _detect_type_conflict(record):
    """Return True if any linked source entity has a cross-type redirect_to.

    A cross-type redirect occurs when a source record's ``redirect_to`` target
    exists (in any entity group, e.g. agents/gnd, places/gnd, concepts/gnd) and
    has a **different** ``bf:type``.  A missing target is not considered a
    conflict — it may simply not have been loaded yet.

    :param record: A MEF DB record (EntityMefRecord subclass).
    :returns: bool
    """
    cls = type(record)
    if not hasattr(cls, "entities"):
        return False

    for entity_name in cls.entities:
        entity_ref = record.get(entity_name)
        if not isinstance(entity_ref, dict) or "$ref" not in entity_ref:
            continue

        ref_url = entity_ref["$ref"]
        ref_pid = ref_url.rstrip("/").rsplit("/", 1)[-1]

        source_class = _get_entity_class_by_ref(ref_url)
        if source_class is None:
            continue

        source_rec = source_class.get_record_by_pid(ref_pid)
        if source_rec is None:
            continue

        rel = source_rec.get("relation_pid")
        if not rel or rel.get("type") != "redirect_to":
            continue

        target_type = _find_source_type(entity_name, rel["value"])
        if target_type is not None and source_rec.get("type") != target_type:
            return True

    return False


def _compute_mef_sort_fields(json):
    """Compute pre-indexed sort fields for MEF records.

    Stores ``sort_authorized_access_point`` (lowercase keyword) and
    ``pid_numeric`` (integer) so searches can sort on native ES fields
    instead of expensive Painless scripts.

    :param json: The ES document dict to mutate in-place.
    """
    # authorized_access_point: prefer top-level, then first matching source
    aap = json.get("authorized_access_point")
    if not aap:
        for src in ("gnd", "idref", "rero"):
            sub = json.get(src)
            if not isinstance(sub, dict):
                continue
            val = sub.get("authorized_access_point")
            if isinstance(val, list):
                val = val[0] if val else None
            if val:
                aap = val
                break
    if aap:
        json["sort_authorized_access_point"] = str(aap).lower()
    else:
        json.pop("sort_authorized_access_point", None)

    # pid_numeric: store pid as integer for proper numeric sort
    try:
        json["pid_numeric"] = int(json["pid"])
    except ValueError, KeyError, TypeError:
        json.pop("pid_numeric", None)


def enrich_mef_data(
    sender,
    json=None,
    record=None,
    index=None,
    doc_type=None,
    arguments=None,
    **dummy_kwargs,
):
    """Signal sent before a MEF record is indexed.

    Computes the ``type_conflict`` flag and pre-indexed sort fields
    (``sort_authorized_access_point``, ``pid_numeric``) on the ES document
    without persisting anything to the database.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    base_index = index.split("-")[0]
    if base_index not in _MEF_INDEXES:
        return

    if entity_name := _MEF_INDEX_TO_ENTITY.get(base_index):
        json["entity"] = entity_name

    if _detect_type_conflict(record):
        json["type_conflict"] = True
    else:
        json.pop("type_conflict", None)

    _compute_mef_sort_fields(json)
