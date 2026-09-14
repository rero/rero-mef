# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test resuming the concept association rebuild."""

import json

import click
import pytest

from rero_mef.concepts.rebuild import declared_association_fields, pids_to_rebuild

PIDS = ["027276643", "040048454", "175232768", "040693422"]


@pytest.mark.parametrize(
    ("from_pid", "expected"),
    [
        # the whole set, in the order `get_all_pids` yields it
        (None, PIDS),
        ("", PIDS),
        # the pid the killed run stopped on is rebuilt again, the ones it committed are not
        ("027276643", PIDS),
        ("175232768", ["175232768", "040693422"]),
        ("040693422", ["040693422"]),
    ],
)
def test_pids_to_rebuild(from_pid, expected):
    """Resuming drops the pids committed before the one the run stopped on."""
    assert pids_to_rebuild(PIDS, from_pid) == expected


def test_pids_to_rebuild_unknown_pid():
    """A pid of another source, or a typo, stops the rebuild instead of doing nothing."""
    with pytest.raises(click.BadParameter):
        pids_to_rebuild(PIDS, "000000000")


def test_declared_association_fields(tmp_path):
    """Only the association fields of a mapping file are read back."""
    mapping_file = tmp_path / "mapping.json"
    mapping_file.write_text(
        json.dumps(
            {
                "mappings": {
                    "properties": {
                        "pid": {"type": "keyword"},
                        "_association_identifier": {"type": "keyword"},
                        "_association_level": {"type": "keyword"},
                    }
                }
            }
        )
    )
    assert declared_association_fields(mapping_file) == {
        "_association_identifier": {"type": "keyword"},
        "_association_level": {"type": "keyword"},
    }


def test_declared_association_fields_without_properties(tmp_path):
    """A mapping file declaring no property at all is not an error."""
    mapping_file = tmp_path / "mapping.json"
    mapping_file.write_text(json.dumps({"mappings": {}}))
    assert declared_association_fields(mapping_file) == {}
