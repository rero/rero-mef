# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating IDREF agent."""

from invenio_search.api import RecordsSearch

from ..api import AgentIndexer, AgentRecord
from .fetchers import idref_id_fetcher
from .minters import idref_id_minter
from .models import AgentIdrefMetadata
from .providers import AgentIdrefProvider


class AgentIdrefSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = "agents_idref"
        doc_types = None
        fields = ("*",)
        facets = {}

        default_filter = None


class AgentIdrefRecord(AgentRecord):
    """Idref agent class."""

    minter = idref_id_minter
    fetcher = idref_id_fetcher
    provider = AgentIdrefProvider
    name = "idref"
    viaf_source_code = "SUDOC"
    viaf_pid_name = "idref_pid"
    model_cls = AgentIdrefMetadata
    search = AgentIdrefSearch

    @classmethod
    def get_online_record(cls, id_, debug=False):
        """Get online record.

        :param id_: Id of online record.
        :param debug: Debug print.
        :returns: record or None
        """
        from .tasks import idref_get_record

        return idref_get_record(id_=id_, debug=debug)


class AgentIdrefIndexer(AgentIndexer):
    """Agent IDREF indexer."""

    record_cls = AgentIdrefRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(
            record_id_iterator, index=AgentIdrefSearch.Meta.index, doc_type="aidref"
        )
