# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2020 RERO
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

from click.testing import CliRunner
from utils import create_and_login_monitoring_user

from rero_mef.cli import tokens_create


def test_cli_access_token(app, client, script_info):
    """Test access token cli."""
    email = create_and_login_monitoring_user(app, client)
    runner = CliRunner()
    res = runner.invoke(
        tokens_create,
        ['-n', 'test', '-u', email, '-t', 'my_token'],
        obj=script_info
    )
    assert res.output.strip().split('\n') == ['my_token']
