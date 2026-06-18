# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Common pytest fixtures and plugins."""

import pytest

pytest_plugins = (
    "celery.contrib.pytest",
    "tests.fixtures.agents_data",
    "tests.fixtures.agents_records",
    "tests.fixtures.concepts_data",
    "tests.fixtures.concepts_records",
    "tests.fixtures.places_data",
    "tests.fixtures.places_records",
)


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


@pytest.fixture(scope="module")
def app_config(app_config):
    """Create temporary instance dir for each test."""
    app_config["CELERY_BROKER_URL"] = "memory://"
    app_config["RATELIMIT_STORAGE_URI"] = "memory://"
    app_config["CACHE_TYPE"] = "simple"
    app_config["ACCOUNTS_SESSION_REDIS_URL"] = "redis://localhost:6379/1"
    app_config["SEARCH_ELASTIC_HOSTS"] = None
    app_config["CELERY_CACHE_BACKEND"] = "memory"
    app_config["CELERY_RESULT_BACKEND"] = "cache"
    app_config["CELERY_TASK_ALWAYS_EAGER"] = True
    app_config["CELERY_TASK_EAGER_PROPAGATES"] = True
    return app_config
