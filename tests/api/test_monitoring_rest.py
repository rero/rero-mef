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

"""Test REST API monitoring."""

import json
import time
from unittest.mock import MagicMock, patch

from flask import url_for
from invenio_accounts.testutils import login_user_via_session

from rero_mef.agents.idref.api import AgentIdrefRecord
from rero_mef.utils import get_timestamp, set_timestamp

from ..utils import create_and_login_monitoring_user


def test_monitoring_es_db_counts(client):
    """Test monitoring es_db_counts."""
    res = client.get(url_for("api_monitoring.es_db_counts"))
    assert res.status_code == 200
    assert json.loads(res.get_data(as_text=True)) == {
        "data": {
            "aggnd": {"db": 0, "db-es": 0, "es": 0, "index": "agents_gnd"},
            "agrero": {"db": 0, "db-es": 0, "es": 0, "index": "agents_rero"},
            "aidref": {"db": 0, "db-es": 0, "es": 0, "index": "agents_idref"},
            "cidref": {"db": 0, "db-es": 0, "es": 0, "index": "concepts_idref"},
            "cognd": {"db": 0, "db-es": 0, "es": 0, "index": "concepts_gnd"},
            "comef": {"db": 0, "db-es": 0, "es": 0, "index": "concepts_mef"},
            "corero": {"db": 0, "db-es": 0, "es": 0, "index": "concepts_rero"},
            "mef": {"db": 0, "db-es": 0, "es": 0, "index": "mef"},
            "viaf": {"db": 0, "db-es": 0, "es": 0, "index": "viaf"},
            "pidref": {"db": 0, "db-es": 0, "es": 0, "index": "places_idref"},
            "plgnd": {"db": 0, "db-es": 0, "es": 0, "index": "places_gnd"},
            "plmef": {"db": 0, "db-es": 0, "es": 0, "index": "places_mef"},
        }
    }


def test_monitoring_check_es_db_counts(app, client, agent_idref_data):
    """Test monitoring check_es_db_counts."""
    res = client.get(url_for("api_monitoring.check_es_db_counts"))
    assert res.status_code == 200
    assert json.loads(res.get_data(as_text=True)) == {"data": {"status": "green"}}

    AgentIdrefRecord.create(
        data=agent_idref_data, delete_pid=False, dbcommit=True, reindex=False
    )
    AgentIdrefRecord.flush_indexes()
    res = client.get(url_for("api_monitoring.check_es_db_counts"))
    assert res.status_code == 200
    assert json.loads(res.get_data(as_text=True)) == {
        "data": {"status": "red"},
        "errors": [
            {
                "code": "DB_ES_COUNTER_MISSMATCH",
                "details": "There are 1 items from aidref missing in ES.",
                "id": "DB_ES_COUNTER_MISSMATCH",
                "links": {
                    "about": "http://localhost/monitoring/check_es_db_counts",
                    "aidref": "http://localhost/monitoring/missing_pids/aidref",
                },
                "title": "DB items counts don't match ES items count.",
            }
        ],
    }

    # this view is only accessible by admin
    res = client.get(url_for("api_monitoring.missing_pids", doc_type="aidref"))
    assert res.status_code == 401

    create_and_login_monitoring_user(app, client)

    res = client.get(url_for("api_monitoring.missing_pids", doc_type="aidref", delay=0))
    assert res.status_code == 200

    assert json.loads(res.get_data(as_text=True)) == {
        "data": {
            "DB": [],
            "ES": ["http://localhost/agents/idref/069774331"],
            "ES duplicate": [],
        }
    }


def test_timestamps(app, client):
    """Test timestamps."""
    time_stamp = set_timestamp("test", msg="test msg")
    assert get_timestamp("test") == {"time": time_stamp, "msg": "test msg"}
    res = client.get(url_for("api_monitoring.timestamps"))
    assert res.status_code == 401

    create_and_login_monitoring_user(app, client)

    res = client.get(url_for("api_monitoring.timestamps"))
    assert res.status_code == 200
    assert json.loads(res.get_data(as_text=True)) == {
        "data": {
            "test": {
                "msg": "test msg",
                "unixtime": time.mktime(time_stamp.timetuple()),
                "utctime": time_stamp.strftime("%Y-%m-%d %H:%M:%S"),
            }
        }
    }


def test_monitoring_forbidden(app, client):
    """Authenticated user without monitoring role receives 403."""
    datastore = app.extensions["invenio-accounts"].datastore
    user = datastore.create_user(email="noperm@test.ch", password="1234", active=True)
    datastore.commit()
    login_user_via_session(client, user=user)
    res = client.get(url_for("api_monitoring.missing_pids", doc_type="aidref"))
    assert res.status_code == 403


def test_monitoring_mef_counts(client):
    """mef_counts endpoint returns data dict with entity counts."""
    res = client.get(url_for("api_monitoring.mef_counts"))
    assert res.status_code == 200
    body = json.loads(res.get_data(as_text=True))
    assert "data" in body


def test_monitoring_missing_pids_invalid_type(app, client):
    """missing_pids with an unregistered doc_type returns an error body."""
    create_and_login_monitoring_user(app, client)
    res = client.get(url_for("api_monitoring.missing_pids", doc_type="invalid_xyz"))
    assert res.status_code == 200
    body = json.loads(res.get_data(as_text=True))
    assert "error" in body
    assert body["error"]["id"] == "DOCUMENT_TYPE_NOT_FOUND"


def test_monitoring_db_connection_counts(app, client):
    """db_connection_counts returns connection stats (mocked DB query)."""
    create_and_login_monitoring_user(app, client)
    mock_result = MagicMock()
    mock_result.first.return_value = (100, 5, 3, 92)
    with patch("rero_mef.monitoring.views.db") as mock_db:
        mock_db.session.execute.return_value = mock_result
        res = client.get(url_for("api_monitoring.db_connection_counts"))
    assert res.status_code == 200
    body = json.loads(res.get_data(as_text=True))
    assert body["data"]["max"] == 100


def test_monitoring_db_connections(app, client):
    """db_connections returns per-connection details (mocked DB query)."""
    create_and_login_monitoring_user(app, client)
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    with patch("rero_mef.monitoring.views.db") as mock_db:
        mock_db.session.execute.return_value = mock_result
        res = client.get(url_for("api_monitoring.db_connections"))
    assert res.status_code == 200
    body = json.loads(res.get_data(as_text=True))
    assert body["data"] == {}


def test_monitoring_redis(app, client):
    """Redis endpoint returns Redis info (mocked)."""
    create_and_login_monitoring_user(app, client)
    mock_redis = MagicMock()
    mock_redis.info.return_value = {"redis_version": "6.0.0"}
    with patch("rero_mef.monitoring.views.Redis") as mock_redis_cls:
        mock_redis_cls.from_url.return_value = mock_redis
        res = client.get(url_for("api_monitoring.redis"))
    assert res.status_code == 200
    body = json.loads(res.get_data(as_text=True))
    assert body["data"]["redis_version"] == "6.0.0"


def test_monitoring_es_indices(app, client):
    """es_indices endpoint returns index listing."""
    create_and_login_monitoring_user(app, client)
    res = client.get(url_for("api_monitoring.elastic_search_indices"))
    assert res.status_code == 200
    body = json.loads(res.get_data(as_text=True))
    assert "data" in body


def test_monitoring_es(app, client):
    """Es endpoint returns cluster health."""
    create_and_login_monitoring_user(app, client)
    res = client.get(url_for("api_monitoring.elastic_search"))
    assert res.status_code == 200
    body = json.loads(res.get_data(as_text=True))
    assert "data" in body
    assert "status" in body["data"]
