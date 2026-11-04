# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test the exit status of the harvest command, which a scheduled job reports."""

from unittest import mock

import pytest
from click.testing import CliRunner
from flask import Flask
from flask.cli import ScriptInfo

from rero_mef.cli import harvestname


@pytest.mark.parametrize(("count", "exit_code"), [(3, 0), (0, 0), (-1, 1)])
def test_harvest_exit_code(count, exit_code):
    harvest_task = mock.Mock(return_value=(count, {}, {}))
    with mock.patch("rero_mef.cli.obj_or_import_string", return_value=harvest_task):
        result = CliRunner().invoke(
            harvestname, ["-n", "concepts.gnd"], obj=ScriptInfo(create_app=lambda: Flask("test"))
        )
    assert result.exit_code == exit_code
