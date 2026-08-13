# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating MEF records."""

from invenio_search.api import RecordsSearch

from rero_mef.api_mef import EntityMefRecord, MefIndexer

from ..utils import get_concept_classes
from .fetchers import mef_id_fetcher
from .minters import mef_id_minter
from .models import ConceptMefMetadata
from .providers import ConceptMefProvider


class ConceptMefSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = "concepts_mef"
        doc_types = None
        fields = ("*",)
        facets = {}

        default_filter = None


class ConceptMefRecord(EntityMefRecord):
    """Mef concept class."""

    minter = mef_id_minter
    fetcher = mef_id_fetcher
    provider = ConceptMefProvider
    name = "mef"
    model_cls = ConceptMefMetadata
    search = ConceptMefSearch
    mef_type = "CONCEPTS"
    entities = ["idref", "rero", "gnd"]

    @classmethod
    def _set_type(cls, data):
        """Set the MEF type.

        :param data: The data to set the type.
        :returns: data
        """
        data["type"] = "bf:Topic"
        concept_classes = get_concept_classes()
        for concept in cls.entities:
            if concept := data.get(concept):
                ref_split = concept["$ref"].split("/")
                ref_type = ref_split[-2]
                ref_pid = ref_split[-1]
                for concept_class in concept_classes.values():
                    if concept_class.name == ref_type:
                        if concept_rec := concept_class.get_record_by_pid(ref_pid):
                            data["type"] = concept_rec["type"]
                        break
        return data

    def update(self, data, commit=False, dbcommit=False, reindex=False):
        """Update data for record.

        :param data: a dict data to update the record.
        :param commit: if True push the db transaction.
        :param dbcommit: make the change effective in db.
        :param reindex: reindex the record.
        :returns: the modified record
        """
        data = self._set_type(data)
        return super().update(data=data, commit=commit, dbcommit=dbcommit, reindex=reindex)

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
        data = cls._set_type(data)
        return super().create(
            data=data,
            id_=id_,
            delete_pid=delete_pid,
            dbcommit=dbcommit,
            reindex=reindex,
            md5=False,
            **kwargs,
        )


class ConceptMefIndexer(MefIndexer):
    """Concept MEF indexer."""

    record_cls = ConceptMefRecord
