# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating RERO agent."""

from invenio_search.api import RecordsSearch

from ..api import AgentIndexer, AgentRecord
from .fetchers import rero_id_fetcher
from .minters import rero_id_minter
from .models import AgentReroMetadata
from .providers import AgentReroProvider


class AgentReroSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = "agents_rero"
        doc_types = None
        fields = ("*",)
        facets = {}

        default_filter = None


class AgentReroRecord(AgentRecord):
    """Rero agent class."""

    minter = rero_id_minter
    fetcher = rero_id_fetcher
    provider = AgentReroProvider
    name = "rero"
    # RERO is obsolete and not linked through VIAF (see ``AgentViafRecord.sources``)
    viaf_source_code = None
    viaf_pid_name = None
    model_cls = AgentReroMetadata
    search = AgentReroSearch


class AgentReroIndexer(AgentIndexer):
    """Agent RERO indexer."""

    record_cls = AgentReroRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, index=AgentReroSearch.Meta.index, doc_type="agrero")
