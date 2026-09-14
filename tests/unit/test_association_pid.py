# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test picking the record an association identifier belongs to."""

import pytest

from rero_mef.api import ConceptPlaceRecord

pick = ConceptPlaceRecord._single_association_pid


@pytest.mark.parametrize(
    ("candidates", "expected"),
    [
        ([], None),
        ([("040048454", "closeMatch")], "040048454"),
        ([("040048454", None)], "040048454"),
        # sixteen camera models close-match one BNF number, none of them wins
        ([("041210778", "closeMatch"), ("041270053", "closeMatch")], None),
        # the single exactMatch beats the close matches of the same number
        ([("040058719", "closeMatch"), ("040693422", "exactMatch")], "040693422"),
        ([("040058719", "closeMatch"), ("040059103", "closeMatch"), ("040693422", "exactMatch")], "040693422"),
        # two records asserting equivalence to the same number decide nothing
        ([("040693422", "exactMatch"), ("040063313", "exactMatch")], None),
        # a source that asserts no level never breaks a tie
        ([("027276643", None), ("027225798", None)], None),
    ],
)
def test_single_association_pid(candidates, expected):
    """Only a lone candidate or a lone exactMatch among several wins."""
    assert pick(candidates) == expected


def test_single_association_pid_ignores_candidate_order():
    """The winner does not depend on the order the search returned the hits in."""
    candidates = [("040058719", "closeMatch"), ("040693422", "exactMatch"), ("040059103", "closeMatch")]
    assert pick(candidates) == pick(list(reversed(candidates))) == "040693422"
