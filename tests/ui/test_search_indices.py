# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test the search indices the suite runs against."""


def test_test_indices_are_single_shard(search):
    """Keep every test index on one shard and no replica.

    Guards the placement as much as the values: a mapping file stating the counts
    itself would win over every template and silently bring the 8 shards back.
    """
    settings = search.indices.get_settings(index="*")
    assert settings, "the fixture created no index"
    counts = {
        index: (config["settings"]["index"]["number_of_shards"], config["settings"]["index"]["number_of_replicas"])
        for index, config in settings.items()
    }
    assert set(counts.values()) == {("1", "0")}, counts
