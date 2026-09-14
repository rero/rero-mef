# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test what makes a MEF record describe nothing."""

import pytest

from rero_mef.agents.mef.api import AgentMefRecord
from rero_mef.concepts.mef.api import ConceptMefRecord
from rero_mef.places.mef.api import PlaceMefRecord

REF = {"$ref": "https://mef.rero.ch/api/concepts/idref/1"}


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        # nothing but bookkeeping: the shape `delete_ref` must not leave behind
        ({"pid": "1", "type": "bf:Topic"}, True),
        ({"pid": "1", "type": "bf:Topic", "md5": "x", "deleted": "2026-01-01"}, True),
        # one entity is enough to keep it
        ({"pid": "1", "type": "bf:Topic", "idref": REF}, False),
        ({"pid": "1", "type": "bf:Topic", "gnd": REF}, False),
        ({"pid": "1", "type": "bf:Topic", "idref": REF, "gnd": REF}, False),
        # an agent MEF held only by its VIAF pid is not an orphan either
        ({"pid": "1", "type": "bf:Person", "viaf_pid": "123"}, False),
    ],
)
def test_is_empty(data, expected):
    """A MEF record is empty only when no entity ref and no VIAF pid are left."""
    assert ConceptMefRecord(dict(data)).is_empty is expected


MEF_CLASSES = [AgentMefRecord, ConceptMefRecord, PlaceMefRecord]


@pytest.mark.parametrize("mef_cls", MEF_CLASSES)
def test_a_mef_record_holding_nothing_is_empty(mef_cls):
    """Every MEF type says the same about a record with no entity at all."""
    assert mef_cls({"pid": "1"}).is_empty is True


@pytest.mark.parametrize(
    ("mef_cls", "entity"),
    [(mef_cls, entity) for mef_cls in MEF_CLASSES for entity in mef_cls.entities],
)
def test_is_empty_covers_every_entity_of_every_mef_type(mef_cls, entity):
    """Each entity the MEF type declares keeps it alive on its own."""
    assert mef_cls({"pid": "1", entity: REF}).is_empty is False
