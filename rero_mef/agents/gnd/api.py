# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating GND agent."""

from invenio_search.api import RecordsSearch

from ..api import AgentIndexer, AgentRecord
from .fetchers import gnd_id_fetcher
from .minters import gnd_id_minter
from .models import AgentGndMetadata
from .providers import AgentGndProvider


class AgentGndSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = "agents_gnd"
        doc_types = None
        fields = ("*",)
        facets = {}

        default_filter = None


class AgentGndRecord(AgentRecord):
    """Gnd agent class."""

    minter = gnd_id_minter
    fetcher = gnd_id_fetcher
    provider = AgentGndProvider
    name = "gnd"
    viaf_pid_name = "gnd_pid"
    viaf_source_code = "DNB"
    model_cls = AgentGndMetadata
    search = AgentGndSearch

    @classmethod
    def get_online_record(cls, id_, debug=False):
        """Get online record.

        :param id_: Id of online record.
        :param debug: Debug print.
        :returns: record or None
        """
        from .tasks import gnd_get_record

        return gnd_get_record(id_=id_, debug=debug)


class AgentGndIndexer(AgentIndexer):
    """Agent GND indexer."""

    record_cls = AgentGndRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(
            record_id_iterator, index=AgentGndSearch.Meta.index, doc_type="aggnd"
        )
