# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Common pytest fixtures and plugins."""

import os
import shutil
import tempfile
from urllib.parse import urlsplit, urlunsplit

import pytest

#: Instance folder of a test run. A development instance states the ports of the stack it serves in its
#: `invenio.cfg`, and `rero_mef.celery` builds an application from that folder the moment it is imported, `.env`
#: naming it through `INVENIO_INSTANCE_PATH`. The variable is pointed at an empty folder of our own before that
#: import can happen, so every application a run builds reads the endpoints stated below. `TEST_INSTANCE_PATH`
#: overrides it, for a run against a real instance folder. Each run gets a folder of its own: what a run leaves
#: there, the webpack manifest stub among it, is written once and would otherwise outlive the code that wrote it.
INSTANCE_PATH = os.environ.get("TEST_INSTANCE_PATH") or tempfile.mkdtemp(prefix="rero-mef-tests-")
os.makedirs(INSTANCE_PATH, exist_ok=True)
os.environ["INVENIO_INSTANCE_PATH"] = INSTANCE_PATH

#: Search hosts of a test run. pytest-invenio reads `SEARCH_HOSTS` for the test application; the application
#: `rero_mef.celery` builds on import gets none of that, so the same value is stated for it as well. Both then
#: drive one cluster, whichever `SEARCH_HOSTS` names.
SEARCH_HOSTS = os.environ.get("SEARCH_HOSTS") or '[{"host": "localhost", "port": 9200}]'
os.environ["SEARCH_HOSTS"] = SEARCH_HOSTS
os.environ["INVENIO_SEARCH_HOSTS"] = SEARCH_HOSTS


@pytest.fixture(scope="session", autouse=True)
def remove_instance_path():
    """Take the instance folder of this run away with it, leaving a stated one alone."""
    yield
    if not os.environ.get("TEST_INSTANCE_PATH"):
        shutil.rmtree(INSTANCE_PATH, ignore_errors=True)


pytest_plugins = (
    "celery.contrib.pytest",
    "tests.blocked_sources",
    "tests.fixtures.agents_data",
    "tests.fixtures.agents_records",
    "tests.fixtures.concepts_data",
    "tests.fixtures.concepts_records",
    "tests.fixtures.places_data",
    "tests.fixtures.places_records",
)

#: One shard and no replica for the test indices, overriding the production-sized
#: `record` template by order. Keeps the cluster green and spares every search the
#: fan-out over eight shards. Mirrors the `init` service of docker-compose.yml.
DEV_SINGLE_SHARD_TEMPLATE = {
    "index_patterns": ["*-*"],
    "order": 100,
    "settings": {"number_of_shards": 1, "number_of_replicas": 0},
}


@pytest.fixture(scope="module")
def search(appctx):
    """Setup and teardown all registered search indices.

    Scope: module

    Overrides pytest_invenio's search fixture to delete existing indices
    before creating, so tests run cleanly even when development-environment
    indices are present. pytest_invenio's _search_create_indexes only catches
    elasticsearch.RequestError, not invenio_search.IndexAlreadyExistsError,
    causing failures whenever the dev ES instance has active indices.
    """
    from invenio_search import current_search, current_search_client

    current_search_client.indices.delete_template("*")
    list(current_search.put_templates())
    # After `put_templates`, which the `delete_template` above wipes.
    current_search_client.indices.put_template("dev-single-shard", body=DEV_SINGLE_SHARD_TEMPLATE)
    list(current_search.delete(ignore=[404]))
    list(current_search.create())
    current_search_client.indices.refresh()

    try:
        yield current_search_client
    finally:
        current_search_client.indices.delete(index="*")
        current_search_client.indices.delete_template("*")


@pytest.fixture(scope="module")
def es(search):
    """Alias for search fixture (backward compat for tests that use es directly)."""
    yield search


#: Redis the tests use, the one `docker-compose.yml` serves. Overridable like the `SEARCH_HOSTS` and
#: `SQLALCHEMY_DATABASE_URI` variables pytest-invenio reads, for a run against another stack:
#: `REDIS_URL=redis://localhost:26379 uv run poe tests`.
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")


@pytest.fixture(scope="module")
def app_config(app_config, search_hosts):
    """Point the test application at the services of the test stack.

    A development instance reaches the tests as well: `rero_mef.celery` loads `.env` when it is imported, which
    states `INVENIO_INSTANCE_PATH`, and that folder's `invenio.cfg` is read before these values. Every endpoint is
    therefore stated here, where the instance cannot send a test run at the stack it serves itself.
    """
    app_config["CELERY_BROKER_URL"] = "memory://"
    app_config["RATELIMIT_STORAGE_URI"] = "memory://"
    app_config["CACHE_TYPE"] = "SimpleCache"
    # The session gets database 1 of whichever server `REDIS_URL` names, whether or not it states one itself.
    app_config["ACCOUNTS_SESSION_REDIS_URL"] = urlunsplit(urlsplit(REDIS_URL)._replace(path="/1"))
    app_config["SEARCH_HOSTS"] = search_hosts
    # `invenio-search` reads this deprecated alias only while `SEARCH_HOSTS` is unset. Nulled so an instance
    # stating the old name cannot reach a cluster of its own.
    app_config["SEARCH_ELASTIC_HOSTS"] = None
    app_config["CELERY_CACHE_BACKEND"] = "memory"
    app_config["CELERY_RESULT_BACKEND"] = "cache"
    app_config["CELERY_TASK_ALWAYS_EAGER"] = True
    app_config["CELERY_TASK_EAGER_PROPAGATES"] = True
    return app_config
