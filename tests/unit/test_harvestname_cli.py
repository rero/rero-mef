# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test the exit code of `invenio oaiharvester harvestname`.

The cronjobs only show a failed harvest when the command exits non-zero.
"""

from unittest import mock

import pytest
from click.testing import CliRunner
from flask import Flask
from flask.cli import ScriptInfo

from rero_mef.cli import harvestname


def run_harvestname(count):
    task = mock.Mock(return_value=(count, {}, {}))
    script_info = ScriptInfo(create_app=lambda: Flask("test"))
    with mock.patch("rero_mef.cli.obj_or_import_string", return_value=task):
        return CliRunner().invoke(harvestname, ["-n", "concepts.gnd"], obj=script_info)


@pytest.mark.parametrize("count", [3, 0])
def test_harvestname_success_prints_count(count):
    res = run_harvestname(count)

    assert res.exit_code == 0, res.output
    assert f"Count: {count}" in res.output


def test_harvestname_failure_exits_non_zero():
    res = run_harvestname(-1)

    assert res.exit_code == 1, res.output
    assert "Harvest concepts.gnd failed" in res.output
    assert "Count:" not in res.output
