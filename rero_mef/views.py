# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Agent MEF views."""

import hashlib
import json as _json

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    redirect,
    request,
    stream_with_context,
    url_for,
)
from invenio_cache import current_cache
from invenio_records_rest.errors import InvalidQueryRESTError
from invenio_search import current_search_client
from opensearchpy.exceptions import NotFoundError

from .agents import AgentMefRecord
from .all_mef import AllMefSearch
from .concepts import ConceptMefRecord
from .places import PlaceMefRecord
from .query import and_search_factory

api_blueprint = Blueprint("api_blueprint", __name__, url_prefix="/")


def _endpoint_for_all_mef_pid(pid_value):
    """Resolve the concrete records-rest endpoint for a MEF PID.

    :param pid_value: PID string.
    :returns: Endpoint name or ``None`` when PID is unknown.
    """
    endpoint_map = (
        (AgentMefRecord, "invenio_records_rest.mef_item"),
        (ConceptMefRecord, "invenio_records_rest.comef_item"),
        (PlaceMefRecord, "invenio_records_rest.plmef_item"),
    )
    return next(
        (
            endpoint
            for record_cls, endpoint in endpoint_map
            if record_cls.get_record_by_pid(pid_value)
        ),
        None,
    )


def _ensure_all_mef_alias():
    """Check whether the all_mef alias or at least one backing index exists.

    Does not create or modify any aliases; alias management is handled by the
    ``all_mef_alias`` CLI command and the application extension at startup.

    :returns: True if the alias or a backing index is reachable, False if none
        of them exist.
    :raises Exception: Re-raises transport or authentication errors so they are
        not silently swallowed as a misleading "alias missing" result.
    """
    alias_name = "all_mef"
    targets = ("mef", "concepts_mef", "places_mef")

    try:
        if current_search_client.indices.exists_alias(name=alias_name):
            return True
    except NotFoundError:
        pass
    except Exception:
        current_app.logger.exception(
            "Unexpected error checking all_mef alias existence"
        )
        raise

    for target in targets:
        try:
            if current_search_client.indices.exists(index=target):
                return True
        except NotFoundError:
            pass
        except Exception:
            current_app.logger.exception(
                "Unexpected error checking index existence for %s", target
            )
            raise

    return False


@api_blueprint.route("/agents/mef/latest/<pid_type>:<pid>")
def agent_mef_get_latest(pid_type, pid):
    """Get the latest MEF agent record for a given PID and type.

    :param pid_type: Type of persistent identifier (e.g., 'idref', 'gnd', 'rero').
    :param pid: The persistent identifier value.
    :returns: JSON response containing the latest MEF agent record.
    """
    return jsonify(AgentMefRecord.get_latest(pid_type=pid_type, pid=pid))


@api_blueprint.route("/agents/mef/updated", methods=["POST"])
def agent_mef_get_updated():
    """Get updated MEF agent records based on posted data.

    Expects JSON payload in request body with update information. Returns a streaming response with updated records.

    :returns: Streaming JSON response with updated MEF agent records.
    """
    data = request.get_json()
    generate = AgentMefRecord.get_updated(data)
    return Response(stream_with_context(generate), content_type="application/json")


@api_blueprint.route("/concepts/mef/latest/<pid_type>:<pid>")
def concept_mef_get_latest(pid_type, pid):
    """Get the latest MEF concept record for a given PID and type.

    :param pid_type: Type of persistent identifier (e.g., 'idref', 'gnd', 'rero').
    :param pid: The persistent identifier value.
    :returns: JSON response containing the latest MEF concept record.
    """
    return jsonify(ConceptMefRecord.get_latest(pid_type=pid_type, pid=pid))


@api_blueprint.route("/concepts/mef/updated", methods=["POST"])
def concept_mef_get_updated():
    """Get updated MEF concept records based on posted data.

    Expects JSON payload in request body with update information. Returns a streaming response with updated records.

    :returns: Streaming JSON response with updated MEF concept records.
    """
    data = request.get_json()
    generate = ConceptMefRecord.get_updated(data)
    return Response(stream_with_context(generate), content_type="application/json")


@api_blueprint.route("/places/mef/latest/<pid_type>:<pid>")
def place_mef_get_latest(pid_type, pid):
    """Get the latest MEF place record for a given PID and type.

    :param pid_type: Type of persistent identifier (e.g., 'idref', 'gnd').
    :param pid: The persistent identifier value.
    :returns: JSON response containing the latest MEF place record.
    """
    return jsonify(PlaceMefRecord.get_latest(pid_type=pid_type, pid=pid))


@api_blueprint.route("/places/mef/updated", methods=["POST"])
def place_mef_get_updated():
    """Get updated MEF place records based on posted data.

    Expects JSON payload in request body with update information. Returns a streaming response with updated records.

    :returns: Streaming JSON response with updated MEF place records.
    """
    data = request.get_json()
    generate = PlaceMefRecord.get_updated(data)
    return Response(stream_with_context(generate), content_type="application/json")


_ENTITY_ENDPOINT = {
    "concepts": "invenio_records_rest.comef_item",
    "places": "invenio_records_rest.plmef_item",
    "agents": "invenio_records_rest.mef_item",
}
_ENTITY_PATH = {
    "concepts": "/concepts/",
    "places": "/places/",
    "agents": "/agents/",
}

_ALL_MEF_CACHE_TTL = 60


def _format_hit(hit):
    """Format a single ES hit into the API response shape.

    Uses the ``entity`` field stored at index time; falls back to the index
    name for records indexed before that field was introduced.

    :param hit: Raw ES hit dict.
    :returns: Formatted hit dict.
    """
    metadata = hit.get("_source", {})
    pid = metadata.get("pid") or hit.get("_id")
    entity = metadata.get("entity")
    if not entity:
        index_name = hit.get("_index", "")
        if "concepts_mef" in index_name:
            entity = "concepts"
        elif "places_mef" in index_name:
            entity = "places"
        else:
            entity = "agents"
    endpoint = _ENTITY_ENDPOINT.get(entity, _ENTITY_ENDPOINT["agents"])
    path = _ENTITY_PATH.get(entity, _ENTITY_PATH["agents"])
    return {
        "id": str(pid),
        "created": metadata.get("_created"),
        "updated": metadata.get("_updated"),
        "entity": entity,
        "links": {"self": url_for(endpoint, pid_value=pid), "preview": f"{path}{pid}"},
        "metadata": metadata,
    }


@api_blueprint.route("/all/mef", strict_slashes=False)
@api_blueprint.route("/all/mef/", strict_slashes=False)
def all_mef_search():
    """Search all MEF indexes through the all_mef alias.

    This is a plain API view (not a RECORDS_REST endpoint).
    """
    size = max(1, min(request.args.get("size", default=20, type=int), 100))
    page = max(1, request.args.get("page", default=1, type=int))

    if not _ensure_all_mef_alias():
        return jsonify(
            {
                "status": 404,
                "message": (
                    "The all_mef alias is missing and no MEF indexes were found. "
                    "Index/load mef, concepts_mef and places_mef first."
                ),
            }
        ), 404

    cache_key = (
        "all_mef:"
        + hashlib.md5(_json.dumps(sorted(request.args.lists())).encode()).hexdigest()
    )
    if cached := current_cache.get(cache_key):
        return jsonify(cached)

    search = AllMefSearch()
    try:
        search, _ = and_search_factory(None, search)
    except InvalidQueryRESTError as e:
        return jsonify(
            {
                "status": 400,
                "message": e.description
                or "The syntax of the search query is invalid.",
            }
        ), 400

    search = search.extra(track_total_hits=True)
    search = search[(page - 1) * size : page * size]
    try:
        response = search.execute().to_dict()
    except NotFoundError:
        return jsonify(
            {
                "status": 404,
                "message": (
                    "No such index or alias [all_mef]. "
                    "Ensure mef/concepts_mef/places_mef indexes exist."
                ),
            }
        ), 404

    total = response.get("hits", {}).get("total", 0)
    if isinstance(total, dict):
        total = total.get("value", 0)

    args = request.args.to_dict(flat=False)
    args["size"] = str(size)
    args.pop("page", None)

    links = {
        "self": url_for(
            "api_blueprint.all_mef_search", page=page, **args, _external=True
        )
    }
    if page * size < total:
        links["next"] = url_for(
            "api_blueprint.all_mef_search", page=page + 1, **args, _external=True
        )
    if page > 1:
        links["prev"] = url_for(
            "api_blueprint.all_mef_search", page=page - 1, **args, _external=True
        )

    result = {
        "hits": {
            "total": total,
            "hits": [_format_hit(h) for h in response.get("hits", {}).get("hits", [])],
        },
        "aggregations": response.get("aggregations", {}),
        "links": links,
    }
    current_cache.set(cache_key, result, timeout=_ALL_MEF_CACHE_TTL)
    return jsonify(result)


@api_blueprint.route("/all/mef/<pid_value>", strict_slashes=False)
def all_mef_item(pid_value):
    """Resolve a PID from all_mef and redirect to its concrete item endpoint."""
    if not (endpoint := _endpoint_for_all_mef_pid(pid_value)):
        return jsonify(
            {
                "status": 404,
                "message": f"PID not found in all_mef: {pid_value}",
            }
        ), 404

    return redirect(url_for(endpoint, pid_value=pid_value, _external=True), code=302)
