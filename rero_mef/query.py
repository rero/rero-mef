# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Query factories for REST API."""

from flask import current_app, request
from invenio_records_rest.errors import InvalidQueryRESTError
from invenio_records_rest.facets import default_facets_factory
from invenio_records_rest.sorter import default_sorter_factory
from opensearch_dsl.query import Q


def and_search_factory(self, search, query_parser=None):
    """Parse query using search DSL query.

    :param self: REST view.
    :param search: Elastic search DSL search instance.
    :returns: Tuple with search instance and URL arguments.
    """

    def _default_parser(qstr=None):
        """Default parser for bare REST ``q`` searches.

        No ``fields`` restriction: this is the parser used by the generic
        REST list routes that rero-ils's ``MEFProxyFactory`` calls directly
        (see ``MEFProxyMixin._get_query_params``). rero-ils already
        field-qualifies most of its own query, but deliberately also
        includes a bare, unqualified fallback fragment (e.g. ``(term)``)
        meant to match broadly. Restricting/boosting ``fields`` here was
        tried to stop a record whose biography merely *mentions* a search
        term (e.g. a "Victor Hugo") from outranking the record actually
        *named* by that term -- but plain BM25 field-length normalization
        already favours a precise short-field match over a long descriptive
        one by a wide margin on its own. The actual bug that made ranking
        look broken was a missing "-" in RECORDS_REST_DEFAULT_SORT's
        "relevance" value (config.py), sorting ``_score`` ascending instead
        of descending -- fixed there instead of adding field-scoping
        complexity here for a problem the sort direction already caused.
        """
        if not qstr:
            return Q()
        return Q(
            "query_string",
            query=qstr,
            default_operator="AND",
        )

    query_string = request.values.get("q")
    query_parser = query_parser or _default_parser

    try:
        search = search.query(query_parser(query_string))
    except SyntaxError:
        current_app.logger.debug(
            f"Failed parsing query: {request.values.get('q', '')}",
            exc_info=True,
        )
        raise InvalidQueryRESTError()

    search_index = search._index[0]
    search, urlkwargs = default_facets_factory(search, search_index)
    search, sortkwargs = default_sorter_factory(search, search_index)
    for key, value in sortkwargs.items():
        urlkwargs.add(key, value)

    urlkwargs.add("q", query_string)

    # Check if deleted records should be included in search results
    # By default, exclude deleted records unless explicitly requested
    with_deleted = request.args.get(
        "with_deleted", default=False, type=lambda v: v.lower() in ["true", "1"]
    )
    if not with_deleted:
        search = search.exclude("exists", field="deleted")

    return search, urlkwargs


_QUERY_STRING_RESERVED_CHARS = '+-=!(){}[]^"~*?:\\/<>'


def _escape_query_string(qstr):
    """Escape Lucene/query_string reserved syntax characters in raw user input.

    Prevents a raw search term from altering clause structure, switching
    fields, or adding boosts when interpolated into a hand-built
    ``query_string`` query. Whitespace is left untouched so multi-word input
    still searches as separate terms.

    :param qstr: raw user-supplied search term.
    :returns: ``qstr`` with reserved characters backslash-escaped.
    """
    escaped = qstr.replace("\\", "\\\\")
    for char in _QUERY_STRING_RESERVED_CHARS.replace("\\", ""):
        escaped = escaped.replace(char, f"\\{char}")
    return escaped.replace("&&", r"\&\&").replace("||", r"\|\|")


def mef_ui_query_parser(qstr=None):
    """Query parser for the MEF UI's own free-text search (``all_mef_search``).

    The MEF UI has no field-qualified query of its own -- unlike API
    consumers such as rero-ils's ``MEFProxyFactory``, which already builds
    one (see ``MEFProxyMixin._get_query_params`` in rero-ils), it only has
    the bare term typed into the search box. Builds that same clause here,
    then hands it to the exact same unrestricted ``Q()`` construction as
    :func:`and_search_factory`'s ``_default_parser`` (no ``fields``), so a
    term typed into the MEF UI ranks results identically to the same term
    arriving from rero-ils's autocomplete.

    :param qstr: the raw search term (or ``None``/empty for a match-all).
    :returns: an elasticsearch_dsl ``Q`` query.
    """
    if not qstr:
        return Q()
    escaped = _escape_query_string(qstr)
    query = (
        f'(idref.authorized_access_point:"{escaped}" OR gnd.authorized_access_point:"{escaped}")^10 '
        f'OR (autocomplete_name:"{escaped}" OR "{escaped}")^4 OR ({escaped})'
    )
    return Q("query_string", query=query, default_operator="AND")
