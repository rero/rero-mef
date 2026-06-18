# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test cli."""

import re
from os.path import dirname, join
from unittest import mock

import pytest
from click.testing import CliRunner

from rero_mef.agents import AgentMefRecord
from rero_mef.cli import (
    clean_multiple_mef,
    create_or_update,
    delete,
    rabbitmq_queue_count,
    tokens_create,
    wait_empty_tasks,
)
from rero_mef.tasks import delete as task_delete

from ..utils import create_and_login_monitoring_user, create_record


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
    assert app
    aggnd_file_name = join(dirname(__file__), "../data/aggnd.json")
    runner = CliRunner()
    res = runner.invoke(
        create_or_update, ["aggnd", aggnd_file_name, "-l", "-v"], obj=script_info
    )
    outputs = res.output.strip().split("\n")
    assert outputs[0] == "Update records: aggnd"
    assert outputs[1] == (
        "1          aggnd  pid:  00401653X                 CREATE | mef: 1 CREATE"
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


def test_cli_clean_multiple_mef_reports_and_deletes_orphans(app, script_info):
    """Test clean_multiple_mef reports and removes orphaned MEF records."""
    assert app

    def _extract_count(output, pattern):
        if match := re.search(pattern, output):
            return int(match.group(1))
        return None

    def assert_orphan_output(output, pid):
        assert "agents-mef orphaned pids:" in output
        assert pid in output
        orphaned = _extract_count(output, r"agents-mef: orphaned=(\d+)")
        assert orphaned is not None
        assert orphaned >= 1
        assert "Detected duplicate entity mappings: 0; orphaned mef records:" in output

    orphan = create_record(
        AgentMefRecord,
        {"$schema": "https://mef.rero.ch/schemas/mef/mef-v0.0.1.json"},
    )
    orphan_pid = str(dict(orphan)["pid"])
    runner = CliRunner()

    res = runner.invoke(
        clean_multiple_mef,
        ["--dry-run", "-r", "aidref", "-v"],
        obj=script_info,
        catch_exceptions=False,
    )
    assert_orphan_output(res.output, orphan_pid)

    res = runner.invoke(
        clean_multiple_mef,
        ["-r", "aidref", "-v"],
        obj=script_info,
        catch_exceptions=False,
    )
    assert "agents-mef orphaned pids:" in res.output
    assert orphan_pid in res.output
    orphaned = _extract_count(res.output, r"agents-mef: orphaned=(\d+)")
    deleted = _extract_count(res.output, r"agents-mef: orphaned=\d+ deleted=(\d+)")
    total_deleted = _extract_count(res.output, r"deleted orphaned mef records: (\d+)")
    assert orphaned is not None and orphaned >= 1
    assert deleted is not None and deleted >= 1
    assert total_deleted is not None and total_deleted >= 1
    assert "Detected duplicate entity mappings: 0; reconciled: 0;" in res.output
    assert AgentMefRecord.get_record_by_pid(orphan_pid) is None


def test_cli_clean_multiple_mef_flushes_before_orphan_scan(app, script_info):
    """Test clean_multiple_mef flushes ES before scanning for orphaned MEF records."""
    assert app
    runner = CliRunner()
    call_order = []
    record = mock.Mock()

    class FakeEntityClass:
        @staticmethod
        def get_record_by_pid(pid):
            call_order.append(("get_record_by_pid", pid))
            return record

    def _create_or_update_mef(*_args, **_kwargs):
        call_order.append("create_or_update_mef")

    def _flush_indexes():
        call_order.append("flush_indexes")

    def _get_orphans():
        call_order.append("get_all_pids_without_entities_and_viaf")
        return iter([])

    record.create_or_update_mef.side_effect = _create_or_update_mef

    with (
        mock.patch(
            "rero_mef.cli.AgentMefRecord.get_multiple_missing_pids",
            return_value=(
                None,
                {"aidref": {"entity-1": ["mef-1", "mef-2"]}},
                None,
                None,
            ),
        ),
        mock.patch(
            "rero_mef.cli.AgentMefRecord.flush_indexes", side_effect=_flush_indexes
        ),
        mock.patch(
            "rero_mef.cli.AgentMefRecord.get_all_pids_without_entities_and_viaf",
            side_effect=_get_orphans,
        ),
        mock.patch(
            "rero_mef.cli.get_entity_class",
            return_value=FakeEntityClass,
        ),
        mock.patch(
            "rero_mef.cli.ConceptMefRecord.get_multiple_missing_pids",
            return_value=(None, {}, None, None),
        ),
        mock.patch(
            "rero_mef.cli.ConceptMefRecord.get_all_pids_without_entities_and_viaf",
            return_value=iter([]),
        ),
        mock.patch(
            "rero_mef.cli.PlaceMefRecord.get_multiple_missing_pids",
            return_value=(None, {}, None, None),
        ),
        mock.patch(
            "rero_mef.cli.PlaceMefRecord.get_all_pids_without_entities_and_viaf",
            return_value=iter([]),
        ),
    ):
        res = runner.invoke(
            clean_multiple_mef,
            ["-r", "aidref"],
            obj=script_info,
            catch_exceptions=False,
        )

    assert res.exit_code == 0
    assert call_order == [
        ("get_record_by_pid", "entity-1"),
        "create_or_update_mef",
        "flush_indexes",
        "get_all_pids_without_entities_and_viaf",
    ]


def test_rabbitmq_queue_count(app):
    """Test RabbitMQ queue message counting via passive queue declarations."""
    assert app
    queues = {"celery": object(), "bulk": object()}
    connection = mock.Mock()
    channel = mock.Mock()
    channel.queue_declare.side_effect = [
        ("celery", 2, 1),
        ("bulk", 3, 1),
    ]
    connection.channel.return_value = channel

    context_manager = mock.MagicMock()
    context_manager.__enter__.return_value = connection
    context_manager.__exit__.return_value = False

    fake_celery = mock.Mock()
    fake_celery.amqp = mock.Mock(queues=queues)
    fake_celery.connection_or_acquire.return_value = context_manager

    with mock.patch("rero_mef.cli.current_celery", fake_celery):
        assert rabbitmq_queue_count() == 5


def test_wait_empty_tasks_checks_rabbitmq(app):
    """Test waiting also checks RabbitMQ pending messages."""
    assert app
    with (
        mock.patch("rero_mef.cli.queue_count", side_effect=[0, 0, 0, 0]),
        mock.patch("rero_mef.cli.rabbitmq_queue_count", side_effect=[1, 0, 0, 0]),
        mock.patch("rero_mef.cli.sleep") as mocked_sleep,
    ):
        wait_empty_tasks(delay=0, verbose=False)
        assert mocked_sleep.call_count == 3


def test_rabbitmq_queue_count_returns_none_on_inspection_error(app):
    """Test RabbitMQ inspection errors are logged and returned as None."""
    assert app
    queues = {"celery": object()}
    connection = mock.Mock()
    channel = mock.Mock()
    channel.queue_declare.side_effect = RuntimeError("broker error")
    connection.channel.return_value = channel

    context_manager = mock.MagicMock()
    context_manager.__enter__.return_value = connection
    context_manager.__exit__.return_value = False

    fake_celery = mock.Mock()
    fake_celery.amqp = mock.Mock(queues=queues)
    fake_celery.connection_or_acquire.return_value = context_manager

    with (
        mock.patch("rero_mef.cli.current_celery", fake_celery),
        mock.patch.object(app.logger, "exception") as mock_exception,
    ):
        assert rabbitmq_queue_count() is None

    channel.close.assert_called_once()
    mock_exception.assert_called_once()


def test_wait_empty_tasks_retries_then_raises_on_inspection_failure(app):
    """Test wait_empty_tasks retries inspection failures before aborting."""
    assert app
    with (
        mock.patch("rero_mef.cli.combined_queue_count", return_value=None),
        mock.patch("rero_mef.cli.sleep") as mocked_sleep,
        mock.patch.object(app.logger, "warning") as mock_warning,
        pytest.raises(RuntimeError, match="Task queue inspection failed repeatedly"),
    ):
        wait_empty_tasks(delay=0, verbose=False)

    assert mocked_sleep.call_args_list == [mock.call(1), mock.call(2)]
    assert mock_warning.call_count == 4
