# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test cli."""

import json
import tempfile
from os.path import dirname, isfile, join
from shutil import copy2
from unittest import mock

import pytest
from click.testing import CliRunner

from rero_mef.agents.cli import (
    _clean_non_existing_viaf_links,
    create_csv_mef,
    create_csv_viaf,
    create_from_viaf,
    harvest_viaf,
)


def test_create_csv_viaf_mef(script_info, tmpdir):
    """Test create CSV VIAF."""
    runner = CliRunner()
    viaf_text_file = join(dirname(__file__), "../../data/viaf.txt")
    output_directory = tempfile.mkdtemp()
    res = runner.invoke(
        create_csv_viaf, [viaf_text_file, output_directory], obj=script_info
    )
    assert res.output.strip().split("\n") == [
        "Create VIAF CSV files.",
        f"  VIAF input file: {viaf_text_file}",
        "  Number of VIAF records created: 859.",
    ]
    viaf_metadata = join(output_directory, "viaf_metadata.csv")
    viaf_pidstore = join(output_directory, "viaf_pidstore.csv")
    assert isfile(viaf_metadata)
    assert isfile(viaf_pidstore)
    with open(viaf_metadata) as in_file:
        metadata_count = 0
        for line in in_file:
            metadata_count += 1
        assert metadata_count == 859
        data = line.strip().split("\t")
        # don't use the first two lines with dates.
        assert data[3:] == [
            '{"bne_pid": "XX871391", '
            '"wiki": ['
            '"https://ar.wikipedia.org/wiki/\\\\u0642\\\\u0627\\\\u064a'
            '_\\\\u0633\\\\u062a\\\\u064a\\\\u0631\\\\u0646", '
            '"https://de.wikipedia.org/wiki/Guy_Stern", '
            '"https://en.wikipedia.org/wiki/Guy_Stern"'
            "], "
            '"rero_pid": "A003863577", '
            '"pid": "108685760", '
            '"$schema": "https://mef.rero.ch/schemas/viaf/viaf-v0.0.1.json"}',
            "1",
        ]
    with open(viaf_pidstore) as in_file:
        pidstore_count = sum(1 for _ in in_file)
        assert pidstore_count == metadata_count

    copy2(join(dirname(__file__), "../../data/aggnd_pidstore.csv"), output_directory)
    copy2(join(dirname(__file__), "../../data/aidref_pidstore.csv"), output_directory)
    copy2(join(dirname(__file__), "../../data/agrero_pidstore.csv"), output_directory)
    res = runner.invoke(
        create_csv_mef, [viaf_metadata, output_directory], obj=script_info
    )
    assert res.output.strip().split("\n") == [
        "Create MEF CSV files from VIAF metadata.",
        f"  VIAF input file: {viaf_metadata}",
        "  Number of MEF records created: 132.",
    ]
    mef_metadata = join(output_directory, "mef_metadata.csv")
    mef_pidstore = join(output_directory, "mef_pidstore.csv")
    mef_id = join(output_directory, "mef_id.csv")
    assert isfile(mef_metadata)
    assert isfile(mef_pidstore)
    assert isfile(mef_id)


def test_harvest_viaf(script_info, agent_viaf_record):
    """Test harvest_viaf CLI command refresh mode."""
    runner = CliRunner()
    with mock.patch("rero_mef.agents.cli.process_viaf_refresh") as mock_viaf_refresh:
        mock_viaf_refresh.return_value = (5, {"UPTODATE": 5})
        res = runner.invoke(
            harvest_viaf,
            ["--progress"],
            obj=script_info,
            catch_exceptions=False,
        )
        assert "VIAF refresh" in res.output
        assert "Processed: 5" in res.output
        mock_viaf_refresh.assert_called_once()


def test_harvest_viaf_enqueue(script_info, agent_viaf_record):
    """Test harvest_viaf CLI command — refresh mode."""
    runner = CliRunner()
    with mock.patch("rero_mef.agents.cli.process_viaf_refresh") as mock_refresh:
        mock_refresh.return_value = (0, {})
        res = runner.invoke(
            harvest_viaf,
            [],
            obj=script_info,
            catch_exceptions=False,
        )
        assert "VIAF refresh" in res.output
        mock_refresh.assert_called_once()


def test_harvest_viaf_rejects_negative_batch_size(script_info):
    """Test harvest_viaf rejects negative batch size values."""
    runner = CliRunner()
    res = runner.invoke(
        harvest_viaf,
        ["--batch_size", "-1"],
        obj=script_info,
    )
    assert res.exit_code != 0
    assert "-1 is not in the range x>=0" in res.output


def test_harvest_viaf_single_pid(script_info):
    """Test harvest_viaf CLI command for a single VIAF PID."""
    runner = CliRunner()
    with mock.patch("rero_mef.agents.cli.viaf_get_record") as mock_get_record:
        mock_get_record.return_value = "UPDATE"
        res = runner.invoke(
            harvest_viaf,
            ["--pid", "123456"],
            obj=script_info,
            catch_exceptions=False,
        )
        assert "VIAF single record harvest: 123456" in res.output
        assert "Processed: 123456" in res.output
        assert "UPDATE" in res.output
        mock_get_record.assert_called_once_with(
            viaf_pid="123456",
            verbose=False,
            progress=False,
            delete_if_not_found=False,
            update_agents=False,
        )


def test_harvest_viaf_rejects_pid_with_batch_size(script_info):
    """Test harvest_viaf rejects combining --pid with --batch_size."""
    runner = CliRunner()
    res = runner.invoke(
        harvest_viaf,
        ["--pid", "123456", "--batch_size", "1"],
        obj=script_info,
    )
    assert res.exit_code != 0
    assert "--pid cannot be combined with --batch_size" in res.output


def test_create_from_viaf_with_enqueue(script_info, agent_viaf_record):
    """Test create_from_viaf with enqueue flag."""
    runner = CliRunner()

    # Test with enqueue flag
    with mock.patch(
        "rero_mef.agents.cli.task_create_mef_and_agents_from_viaf.delay"
    ) as mock_delay:
        mock_delay.return_value = mock.Mock(id="task-123")
        res = runner.invoke(
            create_from_viaf,
            ["--enqueue", "--progress"],
            obj=script_info,
            catch_exceptions=False,
        )
        assert "Create MEF and Agency from VIAF" in res.output
        # Should have enqueued at least one task
        assert mock_delay.call_count >= 1


def test_create_from_viaf_with_viaf_file(app, script_info, tmpdir):
    """Test create_from_viaf with VIAF file input."""
    # Create a temporary VIAF JSON file
    viaf_file = tmpdir.join("test_viaf.json")
    viaf_data = [{"pid": "123456"}, {"pid": "789012"}]
    with open(viaf_file, "w") as f:
        for record in viaf_data:
            f.write(json.dumps(record) + "\n")

    runner = CliRunner()

    # Test with viaf_file
    with mock.patch(
        "rero_mef.agents.cli.task_create_mef_and_agents_from_viaf"
    ) as mock_task:
        res = runner.invoke(
            create_from_viaf,
            ["-f", str(viaf_file), "--progress"],
            obj=script_info,
            catch_exceptions=False,
        )
        assert "Create MEF and Agency from VIAF" in res.output
        # Should process records from file
        assert mock_task.call_count == 2


def test_create_from_viaf_with_viaf_file_cleans_non_existing_pids(script_info, tmpdir):
    """Test create_from_viaf cleans stale VIAF links after sync processing."""
    viaf_file = tmpdir.join("test_viaf.json")
    with open(viaf_file, "w", encoding="utf-8") as file_pointer:
        file_pointer.write(json.dumps({"pid": "123456"}) + "\n")

    runner = CliRunner()
    stale_links = {"mef1": "viaf-1"}
    entity_class = mock.Mock()
    entity_class.count.return_value = 0

    with (
        mock.patch(
            "rero_mef.agents.cli.get_entity_classes",
            return_value={"viaf": entity_class},
        ),
        mock.patch(
            "rero_mef.agents.cli.task_create_mef_and_agents_from_viaf"
        ) as mock_task,
        mock.patch(
            "rero_mef.agents.cli.get_all_missing_viaf_pids",
            return_value=([], stale_links),
        ),
        mock.patch(
            "rero_mef.agents.cli._clean_non_existing_viaf_links",
            return_value=1,
        ) as mock_cleanup,
    ):
        res = runner.invoke(
            create_from_viaf,
            ["-f", str(viaf_file)],
            obj=script_info,
            catch_exceptions=False,
        )

    assert res.exit_code == 0
    assert mock_task.call_count == 1
    mock_cleanup.assert_called_once_with(non_existing_pids=stale_links, verbose=False)
    assert "Clean VIAF pids from MEF records: 1" in res.output
    assert "Cleaned MEF records: 1" in res.output


def test_create_from_viaf_with_enqueue_cleans_non_existing_pids(script_info):
    """Test create_from_viaf cleans stale VIAF links after enqueueing."""
    runner = CliRunner()
    stale_links = {"mef1": "viaf-1"}
    entity_class = mock.Mock()
    entity_class.count.return_value = 1

    with (
        mock.patch(
            "rero_mef.agents.cli.get_entity_classes",
            return_value={"viaf": entity_class},
        ),
        mock.patch(
            "rero_mef.agents.cli.AgentViafRecord.get_all_pids", return_value=["1"]
        ),
        mock.patch(
            "rero_mef.agents.cli.get_all_missing_viaf_pids",
            return_value=([], stale_links),
        ),
        mock.patch(
            "rero_mef.agents.cli.task_create_mef_and_agents_from_viaf.delay"
        ) as mock_delay,
        mock.patch(
            "rero_mef.agents.cli._clean_non_existing_viaf_links",
            return_value=1,
        ) as mock_cleanup,
    ):
        mock_delay.return_value = mock.Mock(id="task-123")
        res = runner.invoke(
            create_from_viaf,
            ["--enqueue"],
            obj=script_info,
            catch_exceptions=False,
        )

    assert res.exit_code == 0
    assert mock_delay.call_count == 1
    mock_cleanup.assert_called_once_with(non_existing_pids=stale_links, verbose=False)
    assert "Clean VIAF pids from MEF records: 1" in res.output
    assert "Cleaned MEF records: 1" in res.output


def test_harvest_viaf_rejects_unlinked_with_batch_size(script_info):
    """Test harvest_viaf rejects --unlinked with --batch_size."""
    runner = CliRunner()
    res = runner.invoke(
        harvest_viaf,
        ["--unlinked", "--batch_size", "10"],
        obj=script_info,
    )
    assert res.exit_code != 0
    assert "--unlinked cannot be combined with --batch_size" in res.output


def test_harvest_viaf_unlinked_uses_unlinked_iterator(script_info):
    """Test harvest_viaf processes unlinked tasks and passes correct length to progressbar."""
    runner = CliRunner()
    tasks = [("1", "DNB", "123")]
    progress_args = {}

    def _progressbar(items, length=0, verbose=False, label=""):
        progress_args["length"] = length
        progress_args["label"] = label
        progress_args["verbose"] = verbose
        yield from items

    with (
        mock.patch("rero_mef.agents.cli.get_unlinked_agents", return_value=tasks),
        mock.patch("rero_mef.agents.cli.progressbar", side_effect=_progressbar),
        mock.patch(
            "rero_mef.agents.cli.AgentViafRecord.get_online_record",
            return_value=({"pid": "viaf-1"}, "ok"),
        ),
        mock.patch(
            "rero_mef.agents.cli.AgentViafRecord.create_or_update",
            return_value=(mock.Mock(), None),
        ),
    ):
        res = runner.invoke(
            harvest_viaf,
            ["--unlinked"],
            obj=script_info,
            catch_exceptions=False,
        )

    assert res.exit_code == 0
    assert "Processed 1 MEF records without VIAF link." in res.output
    assert progress_args["length"] == 1
    assert progress_args["label"] == "VIAF lookup"


def test_harvest_viaf_unlinked_distinguishes_no_record(script_info):
    """Test unlinked lookup keeps no-record misses distinct from failures."""
    runner = CliRunner()
    tasks = [("1", "DNB", "123")]

    with (
        mock.patch("rero_mef.agents.cli.get_unlinked_agents", return_value=tasks),
        mock.patch(
            "rero_mef.agents.cli.AgentViafRecord.get_online_record",
            return_value=({}, "VIAF get: 123 | NO RECORD"),
        ),
    ):
        res = runner.invoke(
            harvest_viaf,
            ["--unlinked", "--verbose"],
            obj=script_info,
            catch_exceptions=False,
        )

    assert res.exit_code == 0
    assert "No VIAF found for mef:1 DNB:123" in res.output
    assert "VIAF lookup failed" not in res.output


def test_harvest_viaf_unlinked_surfaces_lookup_failures(script_info):
    """Test unlinked lookup surfaces request failures distinctly."""
    runner = CliRunner()
    tasks = [("1", "DNB", "123")]

    with (
        mock.patch("rero_mef.agents.cli.get_unlinked_agents", return_value=tasks),
        mock.patch(
            "rero_mef.agents.cli.AgentViafRecord.get_online_record",
            return_value=({}, "VIAF get: 123 | REQUEST ERROR: boom"),
        ),
    ):
        res = runner.invoke(
            harvest_viaf,
            ["--unlinked"],
            obj=script_info,
            catch_exceptions=False,
        )

    assert res.exit_code == 0
    assert "VIAF lookup failed for mef:1 DNB:123" in res.output
    assert "No VIAF found for mef:1 DNB:123" not in res.output


def test_harvest_viaf_unlinked_propagates_unexpected_lookup_errors(script_info):
    """Test unexpected unlinked lookup errors are not swallowed."""
    runner = CliRunner()
    tasks = [("1", "DNB", "123")]

    with (
        mock.patch("rero_mef.agents.cli.get_unlinked_agents", return_value=tasks),
        mock.patch(
            "rero_mef.agents.cli.AgentViafRecord.get_online_record",
            side_effect=ValueError("boom"),
        ),
        pytest.raises(ValueError, match="boom"),
    ):
        runner.invoke(
            harvest_viaf,
            ["--unlinked"],
            obj=script_info,
            catch_exceptions=False,
        )


def test_clean_non_existing_viaf_links_removes_matching_links():
    """Test cleanup removes stale viaf_pid when values still match."""
    mef_record = mock.MagicMock()
    mef_record.get.side_effect = lambda key, default=None: {"viaf_pid": "v123"}.get(
        key, default
    )

    with mock.patch(
        "rero_mef.agents.mef.api.AgentMefRecord.get_record_by_pid",
        return_value=mef_record,
    ):
        cleaned = _clean_non_existing_viaf_links({"mef1": "v123"}, verbose=False)

    assert cleaned == 1
    mef_record.pop.assert_called_once_with("viaf_pid", None)
    mef_record.update.assert_called_once()


def test_clean_non_existing_viaf_links_skips_changed_or_missing_records():
    """Test cleanup skips records when MEF missing or viaf_pid changed."""
    mef_record = mock.MagicMock()
    mef_record.get.side_effect = lambda key, default=None: {"viaf_pid": "v999"}.get(
        key, default
    )

    def _get_record_by_pid(mef_pid):
        if mef_pid == "mef1":
            return mef_record
        return None

    with mock.patch(
        "rero_mef.agents.mef.api.AgentMefRecord.get_record_by_pid",
        side_effect=_get_record_by_pid,
    ):
        cleaned = _clean_non_existing_viaf_links(
            {"mef1": "v123", "mef2": "v456"},
            verbose=False,
        )

    assert cleaned == 0
    mef_record.pop.assert_not_called()
    mef_record.update.assert_not_called()
