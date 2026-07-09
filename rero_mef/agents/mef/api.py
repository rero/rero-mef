# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating MEF records."""

from invenio_search.api import RecordsSearch

from rero_mef.api_mef import EntityMefRecord, MefIndexer
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

    @classmethod
    def get_all_missing_viaf_pids(cls, verbose=False):
        """Get VIAF pids missing from MEF and MEF records with non-existing VIAF pids.

        :param verbose: Verbose output.
        :returns: Tuple of (missing_viaf_pids: list, non_existing_pids: dict).
        """
        return get_all_missing_viaf_pids(verbose=verbose)


class AgentMefIndexer(MefIndexer):
    """Agent MEF indexer."""

    record_cls = AgentMefRecord
