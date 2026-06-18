# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later


"""Json resolvers."""

import jsonresolver

from ....utils import get_host, resolve_record
from ..api import AgentMefRecord


@jsonresolver.route("/api/agents/mef/<path:path>", host=get_host())
def resolve_mef(path):
    """Resolve MEF records."""
    return resolve_record(path, AgentMefRecord)
