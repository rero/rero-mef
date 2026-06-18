# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

ARG VERSION=latest
FROM rero/rero-mef-base:${VERSION}

LABEL maintainer="software@rero.ch"
LABEL description="MEF (Multilingual Entity File) server with records for persons, works, etc. for reuse in integrated library systems (ILS)."

USER 0

COPY ./ ${WORKING_DIR}/src
WORKDIR ${WORKING_DIR}/src
COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}

RUN chown -R invenio:invenio ${WORKING_DIR}

USER 1000

ENV INVENIO_COLLECT_STORAGE='flask_collect.storage.file'
RUN uv run --no-sync ./scripts/bootstrap --deploy
