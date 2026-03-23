# RERO MEF
# Copyright (C) 2026 RERO
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
