<!--
    RERO MEF
    Copyright (C) 2020-2026 RERO

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
-->

# Installation

You need to install `uv`, it will handle the virtual environment creation for the project
in order to sandbox the Python environment, as well as manage the dependency installation,
among other things.

Start all dependent services using docker compose (this will start PostgreSQL,
Elasticsearch 6, RabbitMQ and Redis):

```console
$ docker compose up -d
```

> **Note**
> Make sure you have [enough virtual memory](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html#docker-cli-run-prod-mode)
> for Elasticsearch in Docker:
>
> ```shell
> # Linux
> $ sysctl -w vm.max_map_count=262144
>
> # macOS
> # Docker Desktop: Settings > Resources > Advanced > set vm.max_map_count=262144
> # Or see: https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html#_set_vm_max_map_count_to_at_least_262144
> ```

Next, bootstrap the instance (this will install all Python dependencies and
build all static assets):

```console
$ uv run poe bootstrap
```

Next, create database tables, search indexes and message queues:

```console
$ ./scripts/setup
```

## Running

Start the webserver and the celery worker:

```console
$ ./scripts/server
```

Start a Python shell:

```console
$ ./scripts/console
```

## Upgrading

In order to upgrade an existing instance simply run:

```console
$ ./scripts/update
```

## Testing

Run the test suite via the provided script:

```console
$ uv run poe run_tests
```

By default, end-to-end tests are skipped. You can include the E2E tests like
this:

```console
$ env E2E=yes uv run poe run_tests
```

For more information about end-to-end testing see [pytest-invenio](https://pytest-invenio.readthedocs.io/en/latest/usage.html#running-e2e-tests).

## Production environment

You can use simulate a full production environment using the
`docker-compose.full.yml`. You can start it like this:

```console
$ docker build --rm -t rero-mef-base:latest -f Dockerfile.base .
$ docker compose -f docker-compose.full.yml up -d
```

In addition to the normal `docker-compose.yml`, this one will start:

- HAProxy (load balancer)
- Nginx (web frontend)
- UWSGI (application container)
- Celery (background task worker)
- Flower (Celery monitoring)
