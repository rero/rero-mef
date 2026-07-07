# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test DeletedStateExtension."""

import logging

from rero_mef.extensions.deleted import DeletedStateExtension


class FakeMefRecord(dict):
    """Minimal MEF-like record: a dict with an ``entities`` list."""

    entities = ["viaf", "idref"]

    def replace_refs(self):
        """Simulate a dangling $ref: the linked source no longer exists."""
        return {"viaf": None, "idref": {"deleted": "2025-02-03T10:36:42+00:00"}}


def test_propagate_deleted_skips_dangling_ref():
    """A $ref resolving to None must not crash; a later valid ref still wins."""
    record = FakeMefRecord(pid="1", viaf={"$ref": "..."}, idref={"$ref": "..."})

    assert DeletedStateExtension()._propagate_deleted(record) is True
    assert record["deleted"] == "2025-02-03T10:36:42+00:00"


def test_propagate_deleted_logs_dangling_ref_warning(caplog):
    """A dangling $ref logs a warning naming the entity, record type, and PID.

    Regression test for the warning emitted by _propagate_deleted's except
    branch: it must identify enough to find the offending record, while the
    existing fallback behavior (a later valid ref still wins) keeps working.
    """
    record = FakeMefRecord(pid="1", viaf={"$ref": "..."}, idref={"$ref": "..."})

    with caplog.at_level(logging.WARNING):
        result = DeletedStateExtension()._propagate_deleted(record)

    assert result is True
    assert record["deleted"] == "2025-02-03T10:36:42+00:00"
    assert "Dangling $ref for viaf on FakeMefRecord 1" in caplog.text


def test_propagate_deleted_all_refs_dangling():
    """When every linked ref is dangling, a stale deleted flag is cleared."""

    class AllDangling(FakeMefRecord):
        def replace_refs(self):
            return {"viaf": None, "idref": None}

    record = AllDangling(
        pid="1", viaf={"$ref": "..."}, idref={"$ref": "..."}, deleted="stale"
    )

    assert DeletedStateExtension()._propagate_deleted(record) is True
    assert "deleted" not in record
