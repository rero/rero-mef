# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Facets filters."""

from datetime import date as _date

from invenio_records_rest.errors import InvalidQueryRESTError
from opensearch_dsl import Q


def exists_filter(field):
    """Create a term filter.

    :param field: Field name.
    :returns: Function that returns the Terms query.
    """

    def inner(_values):
        return Q("exists", field=field)

    return inner


def not_exists_filter(field):
    """Create a term filter.

    :param field: Field name.
    :returns: Function that returns the Terms query.
    """

    def inner(_values):
        return Q("bool", must_not=[Q("exists", field=field)])

    return inner


def any_relation_pid_filter():
    """Filter records that have a relation_pid in any source sub-document."""

    def inner(_values):
        return Q(
            "bool",
            should=[
                Q("exists", field="idref.relation_pid"),
                Q("exists", field="gnd.relation_pid"),
                Q("exists", field="rero.relation_pid"),
            ],
            minimum_should_match=1,
        )

    return inner


def type_conflict_filter():
    """Filter records that have a cross-type redirect (type_conflict flag)."""

    def inner(_values):
        return Q("term", type_conflict=True)

    return inner


def and_terms_filter(field):
    """Create a terms filter requiring all selected values.

    :param field: Field name.
    :returns: Function that returns a bool query with ``must`` term clauses.
    """

    def inner(values):
        return Q("bool", must=[Q("term", **{field: value}) for value in values])

    return inner


def year_filter(field):
    """Create a range filter for a year value on a date field.

    :param field: Date field name.
    :returns: Function that accepts a list of year strings and returns a range query.
    """

    def inner(values):
        if not values:
            return Q("match_all")
        year = str(values[0]).strip()[:4]
        return Q("range", **{field: {"gte": f"{year}||/y", "lte": f"{year}||/y"}})

    return inner


def date_range_filter(field):
    """Create a date range filter accepting 'start:end' ISO date format.

    :param field: Date field name.
    :returns: Function that accepts a list with one range string and returns a range query.
    """

    def inner(values):
        if not values:
            return Q("match_all")
        parts = str(values[0]).split(":", 1)
        start = parts[0].strip() if parts else ""
        end = parts[1].strip() if len(parts) > 1 else ""
        range_q = {}
        if start:
            try:
                _date.fromisoformat(start[:10])
            except ValueError:
                err = InvalidQueryRESTError()
                err.description = f"Invalid date: '{start[:10]}'"
                raise err
            range_q["gte"] = start
        if end:
            try:
                _date.fromisoformat(end[:10])
            except ValueError:
                err = InvalidQueryRESTError()
                err.description = f"Invalid date: '{end[:10]}'"
                raise err
            range_q["lte"] = end if "T" in end else f"{end}T23:59:59"
        return Q("match_all") if not range_q else Q("range", **{field: range_q})

    return inner


def all_mef_entity_filter():
    """Filter all_mef records by entity category.

    Supported values are ``agents``, ``concepts`` and ``places``.
    Uses the ``entity`` keyword field stored at index time.
    """
    valid = {"agents", "concepts", "places"}

    def inner(values):
        terms = [str(v).lower() for v in values if str(v).lower() in valid]
        return Q("match_none") if not terms else Q("terms", entity=terms)

    return inner
