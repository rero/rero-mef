# RERO MEF
# Copyright (C) 2020 RERO
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

"""Facets filters."""

from elasticsearch_dsl import Q


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


def multi_exists_filter(fields):
    """Create a filter that checks if any of multiple fields exist.

    :param fields: List of field names.
    :returns: Function that returns a bool query with should clauses.
    """

    def inner(_values):
        return Q(
            "bool",
            should=[Q("exists", field=field) for field in fields],
            minimum_should_match=1,
        )

    return inner


def deleted_entities_agg(fields):
    """Build the ``deleted_entities`` aggregation dict from a list of fields.

    :param fields: List of field names (e.g. ``["idref.deleted", "gnd.deleted"]``).
    :returns: Elasticsearch filter aggregation dict.
    """
    return {
        "filter": {
            "bool": {
                "should": [{"exists": {"field": f}} for f in fields],
                "minimum_should_match": 1,
            }
        }
    }
