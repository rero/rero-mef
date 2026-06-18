# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test monitoring."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from rero_mef.agents.idref.api import AgentIdrefRecord
from rero_mef.monitoring.api import Monitoring
from rero_mef.monitoring.cli import (
    db_connection_counts as db_conn_counts_cmd,
)
from rero_mef.monitoring.cli import (
    db_connections as db_conns_cmd,
)
from rero_mef.monitoring.cli import (
    es as es_cli,
)
from rero_mef.monitoring.cli import (
    es_db_counts_cli,
    es_db_missing_cli,
    mef_counts_cli,
)
from rero_mef.monitoring.cli import (
    es_indices as es_indices_cli,
)
from rero_mef.monitoring.cli import (
    redis as redis_cli,
)
from rero_mef.monitoring.tasks import _last_snapshot, _rate, index_os_stats


def test_monitoring(app, agent_idref_data, script_info):
    """Test monitoring."""
    cli_output = [
        "DB - ES    type      count                      index   count_es",
        "----------------------------------------------------------------",
        "      0   aggnd          0                 agents_gnd          0",
        "      0  agrero          0                agents_rero          0",
        "      1  aidref          1               agents_idref          0",
        "      0  cidref          0             concepts_idref          0",
        "      0   cognd          0               concepts_gnd          0",
        "      0   comef          0               concepts_mef          0",
        "      0  corero          0              concepts_rero          0",
        "      0     mef          0                        mef          0",
        "      0  pidref          0               places_idref          0",
        "      0   plgnd          0                 places_gnd          0",
        "      0   plmef          0                 places_mef          0",
        "      0    viaf          0                       viaf          0",
    ]
    mon = Monitoring(time_delta=0)
    assert mon.get_es_count("xxx") == "No >>xxx<< in ES"
    assert mon.get_db_count("xxx") == "No >>xxx<< in DB"

    idref = AgentIdrefRecord.create(
        data=agent_idref_data, delete_pid=False, dbcommit=True, reindex=False
    )
    idref_pid = idref.pid
    assert mon.get_db_count("aidref") == 1
    assert mon.get_es_count("agents_idref") == 0
    assert mon.check() == {"aidref": {"db_es": 1}}
    assert mon.missing("aidref") == {"DB": [], "ES": ["069774331"], "ES duplicate": []}
    # not flushed by default
    assert mon.info() == {
        "aggnd": {"db": 0, "db-es": 0, "es": 0, "index": "agents_gnd"},
        "agrero": {"db": 0, "db-es": 0, "es": 0, "index": "agents_rero"},
        "aidref": {"db": 1, "db-es": 1, "es": 0, "index": "agents_idref"},
        "cidref": {"db": 0, "db-es": 0, "es": 0, "index": "concepts_idref"},
        "comef": {"db": 0, "db-es": 0, "es": 0, "index": "concepts_mef"},
        "cognd": {"db": 0, "db-es": 0, "es": 0, "index": "concepts_gnd"},
        "corero": {"db": 0, "db-es": 0, "es": 0, "index": "concepts_rero"},
        "mef": {"db": 0, "db-es": 0, "es": 0, "index": "mef"},
        "plgnd": {"db": 0, "db-es": 0, "es": 0, "index": "places_gnd"},
        "pidref": {"db": 0, "db-es": 0, "es": 0, "index": "places_idref"},
        "plmef": {"db": 0, "db-es": 0, "es": 0, "index": "places_mef"},
        "viaf": {"db": 0, "db-es": 0, "es": 0, "index": "viaf"},
    }
    assert mon.__str__().split("\n") == [*cli_output, ""]

    runner = CliRunner()
    res = runner.invoke(es_db_missing_cli, ["aidref", "-d", 0], obj=script_info)
    assert res.output == "ES missing aidref: 069774331\n"

    runner = CliRunner()
    res = runner.invoke(es_db_counts_cli, ["-m", "-d", 0], obj=script_info)
    assert res.output.split("\n") == [
        *cli_output,
        "ES missing aidref: 069774331",
        "",
    ]

    # we have to get the idref again because we lost the session after the use
    # of the CliRunner
    idref = AgentIdrefRecord.get_record_by_pid(idref_pid)
    idref.reindex()
    AgentIdrefRecord.flush_indexes()
    assert mon.get_es_count("agents_idref") == 1
    assert mon.check() == {}
    assert mon.missing("aidref") == {"DB": [], "ES": [], "ES duplicate": []}
    idref.delete(force=True, dbcommit=True)
    assert mon.get_db_count("aidref") == 0
    assert mon.get_es_count("agents_idref") == 1
    assert mon.check() == {"aidref": {"db_es": -1}}
    assert mon.missing("aidref") == {"DB": ["069774331"], "ES": [], "ES duplicate": []}

    # print_missing: DB-missing case (pid in ES but not DB)
    runner = CliRunner()
    res = runner.invoke(es_db_missing_cli, ["aidref", "-d", "0"], obj=script_info)
    assert "DB missing" in res.output


def test_monitoring_print_missing_error(app, script_info):
    """print_missing with unknown doc_type outputs the error message."""
    runner = CliRunner()
    res = runner.invoke(es_db_missing_cli, ["xxx", "-d", "0"], obj=script_info)
    assert "xxx" in res.output
    assert "Error" in res.output


def test_monitoring_info_difference_db_es(app, agent_idref_data):
    """info(difference_db_es=True) is called when DB==ES counts."""
    mon = Monitoring(time_delta=0)
    idref = AgentIdrefRecord.create(
        data=agent_idref_data, delete_pid=False, dbcommit=True, reindex=True
    )
    AgentIdrefRecord.flush_indexes()
    # counts match → difference_db_es branch is entered
    info = mon.info(difference_db_es=True)
    assert "aidref" in info
    # clean up
    idref.delete(force=True, dbcommit=True, delindex=True)
    AgentIdrefRecord.flush_indexes()


def test_monitoring_check_mef(app):
    """check_mef returns a dict with entity-level MEF vs DB counts."""
    mon = Monitoring(time_delta=0)
    result = mon.check_mef()
    assert isinstance(result, dict)


def test_monitoring_cli_mef_counts(app, script_info):
    """mef_counts_cli prints the MEF/DB comparison table."""
    runner = CliRunner()
    res = runner.invoke(mef_counts_cli, ["-d", "0"], obj=script_info)
    assert res.exit_code == 0
    assert "MEF" in res.output


def test_monitoring_cli_es(app, script_info):
    """Es CLI prints ES cluster health info."""
    runner = CliRunner()
    res = runner.invoke(es_cli, [], obj=script_info)
    assert res.exit_code == 0
    assert "status" in res.output


def test_monitoring_cli_es_indices(app, script_info):
    """es_indices CLI outputs index listing without error."""
    runner = CliRunner()
    res = runner.invoke(es_indices_cli, [], obj=script_info)
    assert res.exit_code == 0


def test_monitoring_cli_redis(app, script_info):
    """Redis CLI prints Redis info (mocked)."""
    mock_redis = MagicMock()
    mock_redis.info.return_value = {"redis_version": "6.0.0", "used_memory": 1024}
    with patch("rero_mef.monitoring.cli.Redis") as mock_redis_cls:
        mock_redis_cls.from_url.return_value = mock_redis
        runner = CliRunner()
        res = runner.invoke(redis_cli, [], obj=script_info)
    assert res.exit_code == 0
    assert "redis_version" in res.output


def test_monitoring_cli_db_connection_counts(app, script_info):
    """db_connection_counts CLI prints connection stats (mocked DB query)."""
    mock_result = MagicMock()
    mock_result.first.return_value = (100, 5, 3, 92)
    with patch("rero_mef.monitoring.cli.db") as mock_db:
        mock_db.session.execute.return_value = mock_result
        runner = CliRunner()
        res = runner.invoke(db_conn_counts_cmd, [], obj=script_info)
    assert res.exit_code == 0
    assert "max" in res.output


def test_monitoring_cli_db_connection_counts_error_exits_non_zero(app, script_info):
    """db_connection_counts exits non-zero on DB failure."""
    with patch("rero_mef.monitoring.cli.db") as mock_db:
        mock_db.session.execute.side_effect = Exception("db is down")
        runner = CliRunner()
        res = runner.invoke(db_conn_counts_cmd, [], obj=script_info)
    assert res.exit_code != 0
    assert "db is down" in res.output


def test_monitoring_cli_db_connections(app, script_info):
    """db_connections CLI prints per-connection details (mocked DB query)."""
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        (1, "app", "127.0.0.1", 5432, "t1", "t2", "t3", None, "idle", "x")
    ]
    with patch("rero_mef.monitoring.cli.db") as mock_db:
        mock_db.session.execute.return_value = mock_result
        runner = CliRunner()
        res = runner.invoke(db_conns_cmd, [], obj=script_info)
    assert res.exit_code == 0
    assert "application_name" in res.output


# ---------------------------------------------------------------------------
# rero_mef/monitoring/tasks.py
# ---------------------------------------------------------------------------

_NODE_STATS = {
    "name": "os-node-1",
    "jvm": {
        "mem": {
            "heap_used_percent": 45,
            "heap_used_in_bytes": 512 * 1024 * 1024,
            "heap_max_in_bytes": 1024 * 1024 * 1024,
        },
        "gc": {
            "collectors": {
                "old": {"collection_count": 5, "collection_time_in_millis": 200}
            }
        },
    },
    "os": {"cpu": {"percent": 12}, "mem": {"used_percent": 60}},
    "fs": {"total": {"total_in_bytes": 1_000_000, "free_in_bytes": 600_000}},
    "indices": {
        "docs": {"count": 100_000, "deleted": 50},
        "store": {"size_in_bytes": 512_000},
        "search": {
            "query_total": 500,
            "query_time_in_millis": 1200,
            "fetch_total": 300,
        },
        "indexing": {
            "index_total": 800,
            "index_time_in_millis": 400,
            "index_failed": 2,
        },
    },
}


def _make_client(search_hits=None, raise_on_search=False):
    """Return a mock OpenSearch client for task tests."""
    client = MagicMock()
    client.cluster.health.return_value = {
        "status": "green",
        "active_shards": 10,
        "active_primary_shards": 5,
        "unassigned_shards": 0,
        "relocating_shards": 0,
        "initializing_shards": 0,
        "number_of_nodes": 1,
    }
    client.nodes.stats.return_value = {"nodes": {"node1": _NODE_STATS}}
    if raise_on_search:
        client.search.side_effect = RuntimeError("OS unreachable")
    else:
        hits = search_hits if search_hits is not None else []
        client.search.return_value = {"hits": {"hits": hits}}
    return client


# --- _last_snapshot ----------------------------------------------------------


def test_last_snapshot_returns_source_when_hit_found():
    """Returns _source of first hit when results are present."""
    src = {"@timestamp": "2026-01-01T00:00:00.000Z", "node": {"indices": {}}}
    client = _make_client(search_hits=[{"_source": src}])
    result = _last_snapshot(client, "node1")
    assert result == src


def test_last_snapshot_returns_none_when_no_hits():
    """Returns None when the search result has no hits."""
    client = _make_client(search_hits=[])
    assert _last_snapshot(client, "node1") is None


def test_last_snapshot_returns_none_and_logs_on_exception(caplog):
    """Returns None and logs the exception when the search call fails."""
    import logging

    client = _make_client(raise_on_search=True)
    with caplog.at_level(logging.ERROR, logger="rero_mef.monitoring.tasks"):
        result = _last_snapshot(client, "node1")
    assert result is None
    assert "node1" in caplog.text


# --- _rate -------------------------------------------------------------------


def test_rate_zero_when_no_prev_src():
    """Rate is 0 when there is no previous snapshot (first run)."""
    assert _rate(100, None, "search_query_total", 60) == 0.0


def test_rate_computed_correctly():
    """Rate equals delta / elapsed for a normal transition."""
    prev_src = {"node": {"indices": {"search_query_total": 400}}}
    # (500 - 400) / 60 = 1.6667
    assert _rate(500, prev_src, "search_query_total", 60) == round(100 / 60, 4)


def test_rate_clamped_to_zero_on_negative_delta():
    """Rate is never negative (counter reset / node restart)."""
    prev_src = {"node": {"indices": {"index_total": 1000}}}
    assert _rate(50, prev_src, "index_total", 60) == 0.0


def test_rate_uses_one_when_elapsed_is_zero():
    """elapsed=0 falls back to 1 to avoid division by zero."""
    prev_src = {"node": {"indices": {"index_total": 0}}}
    assert _rate(60, prev_src, "index_total", 0) == 60.0


def test_rate_zero_when_field_missing_in_prev():
    """Missing field in prev_src defaults to current → rate 0."""
    prev_src = {"node": {"indices": {}}}
    assert _rate(200, prev_src, "search_query_total", 60) == 0.0


# --- index_os_stats ----------------------------------------------------------


def test_index_os_stats_first_run_indexes_document():
    """On first run (no snapshot) the task writes one document per node."""
    client = _make_client(search_hits=[])
    with patch("rero_mef.monitoring.tasks.current_search_client", client):
        index_os_stats()
    assert client.index.call_count == 1
    call_kwargs = client.index.call_args
    index_name = call_kwargs[1]["index"] if call_kwargs[1] else call_kwargs[0][0]
    assert index_name.startswith("os-monitor-")


def test_index_os_stats_document_structure():
    """Indexed document contains all expected top-level and nested keys."""
    client = _make_client(search_hits=[])
    with patch("rero_mef.monitoring.tasks.current_search_client", client):
        index_os_stats()
    doc = client.index.call_args[1]["body"]
    assert "@timestamp" in doc
    assert doc["cluster"]["status"] == "green"
    assert doc["cluster"]["status_code"] == 0
    node = doc["node"]
    assert node["id"] == "node1"
    assert "jvm" in node
    assert "os" in node
    assert "fs" in node
    indices = node["indices"]
    assert "search_queries_per_sec" in indices
    assert "index_ops_per_sec" in indices
    assert "index_failures_per_sec" in indices
    assert indices["search_queries_per_sec"] == 0.0
    assert indices["index_ops_per_sec"] == 0.0


def test_index_os_stats_rates_computed_from_prev_snapshot():
    """Rates are non-zero when a previous snapshot provides a baseline."""
    from datetime import UTC, datetime, timedelta

    prev_ts = (datetime.now(UTC) - timedelta(seconds=60)).strftime(
        "%Y-%m-%dT%H:%M:%S.000Z"
    )
    prev_src = {
        "@timestamp": prev_ts,
        "node": {
            "indices": {
                "search_query_total": 400,
                "index_total": 700,
                "index_failed_total": 1,
            }
        },
    }
    client = _make_client(search_hits=[{"_source": prev_src}])
    with patch("rero_mef.monitoring.tasks.current_search_client", client):
        index_os_stats()
    indices = client.index.call_args[1]["body"]["node"]["indices"]
    assert indices["search_queries_per_sec"] > 0
    assert indices["index_ops_per_sec"] > 0
    assert indices["index_failures_per_sec"] > 0


@pytest.mark.parametrize("status,code", [("green", 0), ("yellow", 1), ("red", 2)])
def test_index_os_stats_cluster_status_code(status, code):
    """status_code is mapped correctly for all three cluster health states."""
    client = _make_client(search_hits=[])
    client.cluster.health.return_value = {
        "status": status,
        "active_shards": 1,
        "active_primary_shards": 1,
        "unassigned_shards": 0,
        "relocating_shards": 0,
        "initializing_shards": 0,
        "number_of_nodes": 1,
    }
    with patch("rero_mef.monitoring.tasks.current_search_client", client):
        index_os_stats()
    doc = client.index.call_args[1]["body"]
    assert doc["cluster"]["status"] == status
    assert doc["cluster"]["status_code"] == code
