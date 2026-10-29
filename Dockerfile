# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

ARG VERSION=latest
FROM rero/rero-mef-base:${VERSION}

LABEL maintainer="software@rero.ch"
LABEL description="MEF (Multilingual Entity File) server with records for persons, works, etc. for reuse in integrated library systems (ILS)."

USER 0

COPY ./ ${WORKING_DIR}/src
WORKDIR ${WORKING_DIR}/src

RUN chown -R invenio:invenio ${WORKING_DIR}

USER 1000

ENV LANG=C.UTF-8
RUN uv run --no-sync ./scripts/bootstrap --deploy

# The REST API server, behind nginx. A deployment sizes it with the same variables.
# The access log leaves out the query string: the monitoring passes its token in it.
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
