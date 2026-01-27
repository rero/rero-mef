# RERO MEF
# Copyright (C) 2021 RERO
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

"""Test monitoring."""

from unittest.mock import MagicMock, patch

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
