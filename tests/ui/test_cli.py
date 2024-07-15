# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2024 RERO
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

"""Test cli."""

from os.path import dirname, join

from click.testing import CliRunner
from utils import create_and_login_monitoring_user

from rero_mef.cli import create_or_update, delete, tokens_create
from rero_mef.tasks import delete as task_delete


def test_cli_access_token(app, client, script_info):
    """Test access token cli."""
    email = create_and_login_monitoring_user(app, client)
    runner = CliRunner()
    res = runner.invoke(
        tokens_create, ["-n", "test", "-u", email, "-t", "my_token"], obj=script_info
    )
    assert res.output.strip().split("\n") == ["my_token"]


def test_cli_create_or_update_delete(app, script_info):
    """Test create_or_update and delete cli."""
    aggnd_file_name = join(dirname(__file__), "../data/aggnd.json")
    runner = CliRunner()
    res = runner.invoke(
        create_or_update, ["aggnd", aggnd_file_name, "-l", "-v"], obj=script_info
    )
    outputs = res.output.strip().split("\n")
    assert outputs[0] == "Update records: aggnd"
    assert outputs[1] == (
        "1          aggnd  pid:  00401653X" "                 CREATE | mef: 1 CREATE"
    )

    aggnd_file_name = join(dirname(__file__), "../data/aggnd.json")
    runner = CliRunner()
    res = runner.invoke(
        create_or_update, ["aggnd", aggnd_file_name, "-5", "-v"], obj=script_info
    )
    outputs = res.output.strip().split("\n")
    assert outputs[0] == "Update records: aggnd"
    assert outputs[1] == ("1          aggnd  pid:  00401653X                 UPTODATE")

    aggnd_file_name = join(dirname(__file__), "../data/aggnd.json")
    runner = CliRunner()
    res = runner.invoke(delete, ["aggnd", aggnd_file_name, "-l", "-v"], obj=script_info)
    outputs = res.output.strip().split("\n")
    assert outputs[0] == "Delete records: aggnd"
    assert outputs[1] == ("1          aggnd  pid: 00401653X                 DELETED")

    res = task_delete(0, "test", "aggnd", dbcommit=True, delindex=True, verbose=True)
    assert res == "DELETE NOT FOUND: aggnd test"
