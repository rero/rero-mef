# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating MEF records."""

from copy import deepcopy

from flask import current_app
from invenio_search.api import RecordsSearch

from rero_mef.api import EntityIndexer
from rero_mef.api_mef import EntityMefRecord
from rero_mef.utils import get_entity_classes

from ..api import get_all_missing_viaf_pids
from .fetchers import mef_id_fetcher
from .minters import mef_id_minter
from .models import AgentMefMetadata
from .providers import MefProvider


class AgentMefSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = "mef"
        doc_types = None
        fields = ("*",)
        facets = {}

        default_filter = None


class AgentMefRecord(EntityMefRecord):
    """Mef agent class."""

    minter = mef_id_minter
    fetcher = mef_id_fetcher
    provider = MefProvider
    name = "mef"
    model_cls = AgentMefMetadata
    search = AgentMefSearch
    mef_type = "AGENTS"
    entities = ["idref", "gnd", "rero"]

    @classmethod
    def create(
        cls,
        data,
        id_=None,
        delete_pid=False,
        dbcommit=False,
        reindex=False,
        md5=True,
        **kwargs,
    ):
        """Create a new agent record."""
        data["type"] = "bf:Person"
        entity_classes = get_entity_classes()
        for agent in cls.entities:
            if agent := data.get(agent):
                ref_split = agent["$ref"].split("/")
                ref_type = ref_split[-2]
                ref_pid = ref_split[-1]
                for entity_class in entity_classes.values():
                    if entity_class.name == ref_type:
                        if entity_rec := entity_class.get_record_by_pid(ref_pid):
                            data["type"] = entity_rec["type"]
                        break

        return super().create(
            data=data,
            id_=id_,
            delete_pid=delete_pid,
            dbcommit=dbcommit,
            reindex=reindex,
            md5=False,
            **kwargs,
        )

    def replace_refs(self):
        """Replace $ref with real data."""
        data = deepcopy(self)
        data = super().replace_refs()
        sources = [agent for agent in self.entities if data.get(agent)]
        data["sources"] = sources
        return data

    def add_information(self, resolve=False, sources=False):
        """Add information to record.

        Sources will be also added if resolve is True.
        :param resolve: resolve $refs
        :param sources: Add sources information to record
        :returns: record
        """
        replace_refs_data = AgentMefRecord(deepcopy(self).replace_refs())
        data = replace_refs_data if resolve else deepcopy(self)
        my_sources = []
        for agent in self.entities:
            if agent_data := data.get(agent):
                # we got a error status in data
                if agent_data.get("status"):
                    data.pop(agent)
                    current_app.logger.error(
                        f"MEF replace refs {data.get('pid')} {agent}"
                        f" status: {agent_data.get('status')}"
                        f" {agent_data.get('message')}"
                    )
                else:
                    my_sources.append(agent)
                for agent in self.entities:
                    if agent_data := replace_refs_data.get(agent):
                        if metadata := replace_refs_data[agent].get("metadata"):
                            data[agent] = metadata
        if my_sources and (resolve or sources):
            data["sources"] = my_sources
        return data

    @classmethod
    def get_all_missing_viaf_pids(cls, verbose=False):
        """Get VIAF pids missing from MEF and MEF records with non-existing VIAF pids.

        :param verbose: Verbose output.
        :returns: Tuple of (missing_viaf_pids: list, non_existing_pids: dict).
        """
        return get_all_missing_viaf_pids(verbose=verbose)


class AgentMefIndexer(EntityIndexer):
    """Agent MEF indexer."""

    record_cls = AgentMefRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(
            record_id_iterator, index=AgentMefSearch.Meta.index, doc_type="mef"
        )
