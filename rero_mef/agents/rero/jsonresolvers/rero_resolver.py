# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later


"""Json resolvers."""

import jsonresolver

from ....utils import get_host, resolve_record
from ..api import AgentReroRecord


@jsonresolver.route("/api/agents/rero/<path:path>", host=get_host())
def resolve_rero(path):
    """Resolve RERO records."""
    return resolve_record(path, AgentReroRecord)
