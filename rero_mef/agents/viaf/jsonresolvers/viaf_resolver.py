# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later


"""JSON resolvers."""

import jsonresolver

from ....utils import get_host, resolve_record
from ..api import AgentViafRecord


@jsonresolver.route("/api/agents/viaf/<path:path>", host=get_host())
def resolve_rero(path):
    """Resolve VIAF records."""
    return resolve_record(path, AgentViafRecord)
