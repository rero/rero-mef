# RERO MEF
# Copyright (C) 2026 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.

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
