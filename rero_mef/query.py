# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Query factories for REST API."""

from elasticsearch_dsl.query import Q
from flask import current_app, request
from invenio_records_rest.errors import InvalidQueryRESTError
from invenio_records_rest.facets import default_facets_factory
from invenio_records_rest.sorter import default_sorter_factory


def and_search_factory(self, search, query_parser=None):
    """Parse query using elasticsearch DSL query.

    :param self: REST view.
    :param search: Elastic search DSL search instance.
    :returns: Tuple with search instance and URL arguments.
    """

    def _default_parser(qstr=None):
        """Default parser that uses the Q() from elasticsearch_dsl."""
        if not qstr:
            return Q()
        return Q(
            "query_string",
            query=qstr,
            default_operator="AND",
            fields=[
                "*.authorized_access_point^5",
                "*.variant_access_point^2",
                "*.preferred_name^2",
                "*",
            ],
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
