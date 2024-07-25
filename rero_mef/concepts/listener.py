# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2021 RERO
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

"""Signals connector for Concepts."""


from rero_mef.concepts import ConceptGndSearch, ConceptIdrefSearch
from rero_mef.utils import make_identifier


def enrich_concept_data(
    sender,
    json=None,
    record=None,
    index=None,
    doc_type=None,
    arguments=None,
    **dummy_kwargs,
):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    index_name = index.split("-")[0]
    if index_name in {ConceptGndSearch.Meta.index, ConceptIdrefSearch.Meta.index}:
        for identified_by in json.get("identifiedBy", []):
            identified_by["_identifier"] = make_identifier(identified_by)
        for match_type in {"exactMatch", "closeMatch"}:
            for match in json.get(match_type, []):
                for identified_by in match.get("identifiedBy", []):
                    identified_by["_identifier"] = make_identifier(identified_by)

        if not json.get("deleted") and (
            association_identifier := record.association_identifier
        ):
            json["_association_identifier"] = association_identifier
