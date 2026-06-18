# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later


"""Blueprint used for loading templates."""

from urllib.parse import urlparse

from flask import (
    Blueprint,
    Response,
    abort,
    redirect,
    render_template,
    request,
    url_for,
)

from ..agents.mef.api import AgentMefRecord
from ..concepts.mef.api import ConceptMefRecord
from ..listener import _detect_type_conflict
from ..places.mef.api import PlaceMefRecord
from ..version import __version__


def _same_origin_referrer():
    """Return the referrer URL only when it shares the same host as the current request.

    Prevents open-redirect attacks via a crafted Referer header.
    """
    referrer = request.referrer
    if not referrer:
        return None
    ref_host = urlparse(referrer).netloc
    own_host = urlparse(request.host_url).netloc
    return referrer if ref_host == own_host else None


blueprint = Blueprint(
    "rero_mef",
    __name__,
    template_folder="templates",
    static_folder="static",
)

api_blueprint = Blueprint("api_rero_mef", __name__)

ENTITY_CONFIG = {
    "all_mef": {
        "label": "All MEF",
        "search_api": "/api/all/mef/",
        "search_index": "all_mef",
        "results_template": "templates/rero_mef/all_mef_results.html",
    },
}

_ENTITY_DETAIL_CONFIG = {
    "agents": {
        "label": "Agent MEF",
        "record_cls": AgentMefRecord,
        "api_path": "/api/agents/mef/",
    },
    "concepts": {
        "label": "Concept MEF",
        "record_cls": ConceptMefRecord,
        "api_path": "/api/concepts/mef/",
    },
    "places": {
        "label": "Place MEF",
        "record_cls": PlaceMefRecord,
        "api_path": "/api/places/mef/",
    },
}

_SKIP_FIELDS = frozenset({"$schema", "md5", "_created", "_updated", "sources"})

_DETAIL_ENDPOINT = {
    "agents": "rero_mef.agent_detail",
    "concepts": "rero_mef.concept_detail",
    "places": "rero_mef.place_detail",
}

_LATEST_ENDPOINT = {
    "agents": "rero_mef.agent_latest",
    "concepts": "rero_mef.concept_latest",
    "places": "rero_mef.place_latest",
}

_OLDER_ENDPOINT = {
    "agents": "rero_mef.agent_older",
    "concepts": "rero_mef.concept_older",
    "places": "rero_mef.place_older",
}

# Fields on the top-level MEF record that serve as the inter-source link key.
_MAIN_LINKING_FIELDS = {
    "agents": {"viaf_pid"},
    "concepts": set(),
    "places": set(),
}


# Per-(entity_type, source) predicate deciding which identifiedBy items are link keys.
def _make_id_linking_fn(entity_type, src):
    if entity_type == "agents":
        return lambda item: item.get("source") == "VIAF"
    if entity_type == "concepts" and src == "idref":
        return lambda item: item.get("source") == "BNF" and item.get("type") != "uri"
    if entity_type == "places" and src == "idref":
        return lambda item: item.get("source") == "GND" and item.get("type") == "bf:Nbn"
    return None


# Per-(entity_type, source) set of plain fields that are link keys.
def _source_linking_fields(entity_type, src):
    return {"pid"} if entity_type == "places" and src == "gnd" else set()


# Per-(entity_type, source) BNF source for exactMatch/closeMatch link key highlighting.
def _source_match_link_src(entity_type, src):
    return "BNF" if entity_type == "concepts" and src == "gnd" else None


def _dict_to_text(d):
    """Convert a nested dict to a compact human-readable string."""
    if not isinstance(d, dict):
        return str(d)
    if "authorized_access_point" in d:
        return d["authorized_access_point"]
    if "label" in d:
        raw = d["label"]
        labels = raw if isinstance(raw, list) else [raw]
        text = " | ".join(str(s) for s in labels)
        note_type = d.get("noteType", "")
        return f"{text} [{note_type}]" if note_type else text
    if "classificationPortion" in d:
        portion, cls_type = d["classificationPortion"], d.get("type", "")
        return f"{portion} ({cls_type})" if cls_type else portion
    if "value" in d:
        source = d.get("source", "")
        return f"{d['value']} [{source}]" if source else str(d["value"])
    parts = [f"{k}: {v}" for k, v in d.items() if not isinstance(v, (list, dict))]
    return " | ".join(parts) if parts else str(d)


def _match_identifier_items(match_list, link_src):
    """Build identifier_items from exactMatch/closeMatch entries.

    Each item shows the access point plus the value of the first non-URI
    identifier whose source equals *link_src*. Items that carry such an
    identifier are marked as linking (link key badge).
    """
    items = []
    for match in match_list:
        aap = match.get("authorized_access_point", "")
        if link_id := next(
            (
                i
                for i in match.get("identifiedBy", [])
                if i.get("source") == link_src and i.get("type") != "uri"
            ),
            None,
        ):
            val = link_id.get("value", "")
            url = val if val.startswith("http") else None
            text = f"{aap} [{val}]" if (aap and val) else (aap or val)
            items.append({"url": url, "text": text, "linking": True})
        elif aap:
            items.append({"url": None, "text": aap, "linking": False})
    return [item for item in items if item["text"]]


_MATCH_FIELDS = frozenset({"exactMatch", "closeMatch"})

_REDIRECT_ICONS = {
    "redirect_to": '<i class="fa fa-arrow-right" aria-hidden="true"></i>',
    "redirect_from": '<i class="fa fa-arrow-left" aria-hidden="true"></i>',
}


def _field_to_row(key, label, value, ctx):
    """Convert a single record field into a template row dict, or None to skip."""
    id_linking_fn = ctx.get("id_linking_fn")
    match_link_src = ctx.get("match_link_src")
    base = {"label": label, "bold": key in ctx.get("bold_fields", set())}
    if key == "identifiedBy" and isinstance(value, list):
        items = [
            {
                "url": item.get("value")
                if str(item.get("value", "")).startswith("http")
                else None,
                "text": item.get("value", ""),
                "linking": id_linking_fn(item) if id_linking_fn else False,
            }
            for item in value
        ]
        return {**base, "identifier_items": items} if items else None
    if key in _MATCH_FIELDS and isinstance(value, list) and match_link_src:
        items = _match_identifier_items(value, match_link_src)
        return {**base, "identifier_items": items} if items else None
    if isinstance(value, list):
        str_items = (
            [_dict_to_text(v) for v in value]
            if (value and isinstance(value[0], dict))
            else [str(v) for v in value if v is not None]
        )
        return {**base, "list_items": str_items} if str_items else None
    if isinstance(value, dict):
        if "type" in value and "value" in value:
            if icon := _REDIRECT_ICONS.get(value["type"]):
                text = f"{icon} {value['value']}"
                raw_html = True
            else:
                text = f"{value['type']}: {value['value']}"
                raw_html = False
        else:
            text = _dict_to_text(value)
            raw_html = False
        row = {**base, "value": text, "raw_html": raw_html}
        if key == "relation_pid":
            if rel_url := ctx.get("relation_pid_url"):
                row |= {"url": rel_url, "internal": True}
            elif conflict_url := ctx.get("relation_pid_conflict_url"):
                row |= {"conflict_url": conflict_url}
        return row
    if items := ctx.get("identifier_override", {}).get(key):
        return {**base, "identifier_items": items}
    if value is not None:
        return {
            **base,
            "value": str(value),
            "linking": key in ctx.get("linking_fields", set()),
        }
    return None


_FIRST_FIELDS = ("authorized_access_point",)
_BOLD_FIELDS = frozenset({"authorized_access_point"})


def _build_rows(
    data,
    linking_fields=None,
    id_linking_fn=None,
    match_link_src=None,
    relation_pid_url=None,
    relation_pid_conflict_url=None,
    identifier_override=None,
):
    """Convert a record dict into row dicts consumed by mef_detail.html."""
    linking_fields = linking_fields or set()
    ctx = {
        "id_linking_fn": id_linking_fn,
        "match_link_src": match_link_src,
        "linking_fields": linking_fields,
        "bold_fields": _BOLD_FIELDS,
        "relation_pid_url": relation_pid_url,
        "relation_pid_conflict_url": relation_pid_conflict_url,
        "identifier_override": identifier_override or {},
    }
    ordered = [k for k in _FIRST_FIELDS if k in data] + [
        k for k in data if k not in _FIRST_FIELDS
    ]
    rows = []
    for key in ordered:
        value = data[key]
        if key in _SKIP_FIELDS or key.startswith("$"):
            continue
        label = key.replace("_", " ").title()
        if row := _field_to_row(key, label, value, ctx):
            rows.append(row)
    return rows


def _relation_pid_detail_url(entity_type, rel, record_cls, src):
    """Return (normal_url, conflict_url) for a source relation_pid target.

    ``normal_url`` links to a same-entity-type MEF record; ``conflict_url`` links to a
    MEF record in a different entity type when the target belongs there instead.
    Exactly one of the two is set; both are None when the target is not found anywhere.
    """
    if not rel or not (target := rel.get("value")):
        return None, None
    pids = record_cls.get_mef(target, src, pid_only=True)
    if pids:
        return url_for(_DETAIL_ENDPOINT[entity_type], pid_value=pids[0]), None
    for other_type, other_cls in _ENTITY_DETAIL_CONFIG.items():
        if other_type == entity_type:
            continue
        pids = other_cls["record_cls"].get_mef(target, src, pid_only=True)
        if pids:
            return None, url_for(_DETAIL_ENDPOINT[other_type], pid_value=pids[0])
    return None, None


def _compute_nav_urls(entity_type, record_cls, entities, resolved):
    """Return (latest_url, older_url) navigation links for a MEF detail page.

    Handles two redirect patterns:
    - ``redirect_to`` on source (GND): source is old; latest points to current.
    - ``redirect_from`` on source (IDREF): source is current; older points to old record.
    - Reverse lookup: search for records whose source ``redirect_to`` points at this
      record's source PID, covering the GND case on the current/newer record.
    """
    latest_url = None
    older_url = None
    for src in entities:
        src_data = resolved.get(src)
        if not isinstance(src_data, dict):
            continue
        if rel := src_data.get("relation_pid"):
            rel_type, rel_value = rel.get("type"), rel.get("value")
            if rel_value and rel_type in ("redirect_to", "redirect_from"):
                if record_cls.get_mef(rel_value, src, pid_only=True):
                    if rel_type == "redirect_to":
                        latest_url = url_for(
                            _LATEST_ENDPOINT[entity_type], pid_type=src, pid=rel_value
                        )
                    else:
                        older_url = url_for(
                            _OLDER_ENDPOINT[entity_type], pid_type=src, pid=rel_value
                        )
        if not older_url and (src_pid := src_data.get("pid")):
            for hit in (
                record_cls.search()
                .filter("term", **{f"{src}__relation_pid__value": src_pid})
                .scan()
            ):
                hit_src = hit.to_dict().get(src, {})
                if hit_src.get("relation_pid", {}).get("type") == "redirect_to":
                    if older_src_pid := hit_src.get("pid"):
                        older_url = url_for(
                            _OLDER_ENDPOINT[entity_type],
                            pid_type=src,
                            pid=older_src_pid,
                        )
                        break
        if latest_url and older_url:
            break
    return latest_url, older_url


def _mef_detail(entity_type, pid_value):
    """Shared handler for agent/concept/place MEF detail pages."""
    config = _ENTITY_DETAIL_CONFIG.get(entity_type)
    if not config:
        abort(404)

    record = config["record_cls"].get_record_by_pid(pid_value)
    if record is None:
        abort(404)

    resolved = record.add_information(resolve=True, sources=True)
    item_url = f"{config['api_path']}{pid_value}"
    entity_names = set(record.entities)

    identifier_override = {}
    if entity_type == "agents" and (viaf_pid := resolved.get("viaf_pid")):
        identifier_override["viaf_pid"] = [
            {
                "url": f"/api/agents/viaf/{viaf_pid}",
                "text": str(viaf_pid),
                "linking": True,
            },
            {
                "url": f"http://www.viaf.org/viaf/{viaf_pid}",
                "text": "viaf.org",
                "linking": False,
            },
        ]

    main_rows = _build_rows(
        {k: v for k, v in resolved.items() if k not in entity_names},
        linking_fields=_MAIN_LINKING_FIELDS.get(entity_type, set()),
        identifier_override=identifier_override,
    )

    source_sections = []
    for src in record.entities:
        if src not in resolved or not isinstance(resolved[src], dict):
            continue
        rel_url, conflict_url = _relation_pid_detail_url(
            entity_type, resolved[src].get("relation_pid"), config["record_cls"], src
        )
        source_sections.append(
            {
                "title": src.upper(),
                "url": urlparse(record.get(src, {}).get("$ref", "")).path or None,
                "rows": _build_rows(
                    resolved[src],
                    linking_fields=_source_linking_fields(entity_type, src),
                    id_linking_fn=_make_id_linking_fn(entity_type, src),
                    match_link_src=_source_match_link_src(entity_type, src),
                    relation_pid_url=rel_url,
                    relation_pid_conflict_url=conflict_url,
                ),
            }
        )

    latest_url, older_url = _compute_nav_urls(
        entity_type, config["record_cls"], record.entities, resolved
    )
    type_conflict = _detect_type_conflict(record)

    return render_template(
        "rero_mef/mef_detail.html",
        version=__version__,
        home_url=url_for("rero_mef.all_mef_list"),
        back_url=_same_origin_referrer() or url_for("rero_mef.all_mef_list"),
        latest_url=latest_url,
        older_url=older_url,
        entity_label=config["label"],
        type_conflict=type_conflict,
        item_url=item_url,
        main_rows=main_rows,
        created=record.created.isoformat() if record.created else None,
        updated=record.updated.isoformat() if record.updated else None,
        source_sections=source_sections,
    )


@blueprint.route("/robots.txt")
def robots():
    """Serve robots.txt disallowing all UI paths."""
    content = "User-agent: *\nDisallow: /\nDisallow: /all\n"
    return Response(content, mimetype="text/plain")


@blueprint.route("/")
def index():
    """Home Page."""
    return render_template("rero_mef/frontpage.html", version=__version__)


@blueprint.route("/linking")
def linking():
    """MEF linking mechanisms overview page."""
    return render_template("rero_mef/mef_graph.html", version=__version__)


@blueprint.route("/all")
def all_mef_list():
    """All MEF combined list search page."""
    return _render_entity_list("all_mef")


def _render_entity_list(entity_name):
    """Render entity list page backed by invenio-search-ui components."""
    config = ENTITY_CONFIG[entity_name]
    return render_template(
        "rero_mef/mef_search.html",
        version=__version__,
        entity_name=entity_name,
        entity_label=config["label"],
        search_api=config["search_api"],
        search_index=config["search_index"],
        results_template=config["results_template"],
    )


def _mef_redirect_by_source_pid(entity_type, pid_type, pid):
    """Redirect to the MEF detail page for a given source PID."""
    config = _ENTITY_DETAIL_CONFIG.get(entity_type)
    if not config:
        abort(404)
    pids = config["record_cls"].get_mef(pid, pid_type, pid_only=True)
    if not pids:
        abort(404)
    return redirect(url_for(_DETAIL_ENDPOINT[entity_type], pid_value=pids[0]))


@blueprint.route("/agents/<pid_value>")
def agent_detail(pid_value):
    """Agent MEF detail page."""
    return _mef_detail("agents", pid_value)


@blueprint.route("/agents/latest/<pid_type>:<pid>")
def agent_latest(pid_type, pid):
    """Redirect to the latest agent MEF record for a given source PID."""
    return _mef_redirect_by_source_pid("agents", pid_type, pid)


@blueprint.route("/agents/older/<pid_type>:<pid>")
def agent_older(pid_type, pid):
    """Redirect to the older agent MEF record for a given source PID."""
    return _mef_redirect_by_source_pid("agents", pid_type, pid)


@blueprint.route("/concepts/<pid_value>")
def concept_detail(pid_value):
    """Concept MEF detail page."""
    return _mef_detail("concepts", pid_value)


@blueprint.route("/concepts/latest/<pid_type>:<pid>")
def concept_latest(pid_type, pid):
    """Redirect to the latest concept MEF record for a given source PID."""
    return _mef_redirect_by_source_pid("concepts", pid_type, pid)


@blueprint.route("/concepts/older/<pid_type>:<pid>")
def concept_older(pid_type, pid):
    """Redirect to the older concept MEF record for a given source PID."""
    return _mef_redirect_by_source_pid("concepts", pid_type, pid)


@blueprint.route("/places/<pid_value>")
def place_detail(pid_value):
    """Place MEF detail page."""
    return _mef_detail("places", pid_value)


@blueprint.route("/places/latest/<pid_type>:<pid>")
def place_latest(pid_type, pid):
    """Redirect to the latest place MEF record for a given source PID."""
    return _mef_redirect_by_source_pid("places", pid_type, pid)


@blueprint.route("/places/older/<pid_type>:<pid>")
def place_older(pid_type, pid):
    """Redirect to the older place MEF record for a given source PID."""
    return _mef_redirect_by_source_pid("places", pid_type, pid)
