# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

FROM python:3.14-slim-bookworm

LABEL maintainer="software@rero.ch"
LABEL description="MEF (Multilingual Entity File) server with records for persons, works, etc. for reuse in integrated library systems (ILS)."

RUN apt-get update -y && apt-get upgrade -y \
    && apt-get install --no-install-recommends -y vim-tiny curl procps \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip uv

ENV WORKING_DIR=/invenio
ENV INVENIO_INSTANCE_PATH=${WORKING_DIR}/var/instance
RUN useradd invenio --uid 1000 --home ${WORKING_DIR} \
    && mkdir -p ${INVENIO_INSTANCE_PATH} ${WORKING_DIR}/src \
    && chown -R invenio:invenio ${WORKING_DIR} \
    && chmod -R go+w ${WORKING_DIR}
WORKDIR ${WORKING_DIR}/src
USER 1000

# Without UV_NO_SYNC, `uv run` would install the dev group.
ENV LANG=C.UTF-8 \
    UV_NO_CACHE=1 \
    UV_NO_SYNC=1

COPY --chown=invenio:invenio pyproject.toml uv.lock ./
RUN uv sync --frozen --no-group dev --group prod --no-install-project

COPY --chown=invenio:invenio ./ ./
RUN uv run --no-sync ./scripts/bootstrap --deploy

# The access log leaves out the query string, which holds the monitoring token.
ENV GRANIAN_INTERFACE=wsgi \
    GRANIAN_HOST=0.0.0.0 \
    GRANIAN_PORT=5001 \
    GRANIAN_WORKERS=4 \
    GRANIAN_BLOCKING_THREADS=4 \
    GRANIAN_WORKERS_MAX_RSS=666 \
    GRANIAN_RESPAWN_FAILED_WORKERS=true \
    GRANIAN_LOG_ACCESS_ENABLED=true \
    GRANIAN_LOG_ACCESS_FMT='%(header{x-forwarded-for})s [%(time)s] "%(method)s %(path)s %(protocol)s" %(status)d %(dt_ms).0fms "%(header{user-agent})s"'
CMD ["uv", "run", "--no-sync", "granian", "invenio_app.wsgi_rest:application"]
