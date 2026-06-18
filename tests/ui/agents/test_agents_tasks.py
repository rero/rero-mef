# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for agents/tasks.py."""

from unittest import mock

from rero_mef.agents.tasks import task_create_mef_and_agents_from_viaf


@mock.patch(
    "rero_mef.agents.tasks.AgentViafRecord.get_record_by_pid", return_value=None
)
def test_task_viaf_not_found(mock_get_record, app):
    """task_create_mef_and_agents_from_viaf returns ({}, {}) for unknown pid."""
    result = task_create_mef_and_agents_from_viaf("DOES_NOT_EXIST")
    assert result == ({}, {})
