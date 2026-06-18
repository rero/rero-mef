# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Search API class for the all_mef alias."""

from invenio_search.api import RecordsSearch


class AllMefSearch(RecordsSearch):
    """RecordsSearch over the all_mef alias."""

    class Meta:
        """Search only on all_mef alias."""

        index = "all_mef"
        doc_types = None
        fields = ("*",)
        facets = {}

        default_filter = None
