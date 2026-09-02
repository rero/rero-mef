# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

ARG VERSION=latest

# ---------------------------------------------------------------------------
# Builder: installs dependencies and builds the web assets using the
# toolchain (gcc, Node.js, git, uv) provided by the base image.
# ---------------------------------------------------------------------------
FROM rero/rero-mef-base:${VERSION} AS builder

USER 0

COPY ./ ${WORKING_DIR}/src
WORKDIR ${WORKING_DIR}/src
COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}

RUN chown -R invenio:invenio ${WORKING_DIR}

USER 1000

ENV LANG=C.UTF-8
ENV INVENIO_COLLECT_STORAGE='flask_collect.storage.file'
RUN uv run --no-sync ./scripts/bootstrap --deploy

# ---------------------------------------------------------------------------
# Runtime: only the built virtualenv, static assets and app code - no
# compilers, Node.js, git or editors.
# ---------------------------------------------------------------------------
FROM python:3.14-slim-bookworm AS runtime

LABEL maintainer="software@rero.ch"
LABEL description="MEF (Multilingual Entity File) server with records for persons, works, etc. for reuse in integrated library systems (ILS)."

ENV WORKING_DIR=/invenio
ENV INVENIO_INSTANCE_PATH=${WORKING_DIR}/var/instance

RUN mkdir -p ${INVENIO_INSTANCE_PATH} && \
    useradd invenio --uid 1000 --home ${WORKING_DIR} && \
    chown -R invenio:invenio ${WORKING_DIR} && \
    chmod -R go+w ${WORKING_DIR}

COPY --from=builder /usr/local/bin/uv /usr/local/bin/uvx /usr/local/bin/
COPY --from=builder --chown=invenio:invenio ${WORKING_DIR}/src ${WORKING_DIR}/src
COPY --from=builder --chown=invenio:invenio ${INVENIO_INSTANCE_PATH} ${INVENIO_INSTANCE_PATH}

WORKDIR ${WORKING_DIR}/src
USER 1000
