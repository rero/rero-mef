# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test that mapping files haven't drifted from rero_mef.mapping_analysis.

Guards against the exact bug that motivated that module: the shared French/
German search-analysis filter chain was hand-copied into 11 mapping files,
and ``ascii_folding`` silently went missing from 8 of them. If someone edits
a mapping file's analysis settings directly instead of through
mapping_analysis.MAPPING_SPECS, this test catches the drift immediately.
"""

import pytest

from rero_mef.mapping_analysis import MAPPING_SPECS, REPO_ROOT, apply_spec, check_all


def test_all_mappings_match_their_spec():
    """Every mapping file's analysis settings must match its generated spec."""
    mismatches = check_all()
    paths = [path for path, _, _ in mismatches]
    assert not mismatches, (
        f"{len(mismatches)} mapping file(s) out of sync with their spec "
        f"(run `uv run python -m rero_mef.mapping_analysis write` to fix): {paths}"
    )


@pytest.mark.parametrize("spec", MAPPING_SPECS, ids=[spec["path"] for spec in MAPPING_SPECS])
def test_spec_paths_exist(spec):
    """Every configured spec must point at a real file (catches typos/renames)."""
    assert (REPO_ROOT / spec["path"]).is_file()


def test_apply_spec_keeps_other_sub_fields():
    """Applying a spec must add `raw` without dropping other sub-fields."""
    mapping = {
        "mappings": {
            "properties": {
                "authorized_access_point": {
                    "type": "text",
                    "fields": {"sort": {"type": "icu_collation_keyword"}},
                }
            }
        }
    }
    spec = {
        "kind": "standalone",
        "language": "french",
        "fields": ["authorized_access_point"],
        "add_raw": True,
    }

    patched = apply_spec(mapping, spec)["mappings"]["properties"]["authorized_access_point"]
    assert patched["fields"] == {
        "sort": {"type": "icu_collation_keyword"},
        "raw": {"type": "keyword"},
    }
