# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later


"""Json resolvers."""

import jsonresolver

from rero_mef.utils import get_host, resolve_record

from ..api import AgentGndRecord


@jsonresolver.route("/api/agents/gnd/<path:path>", host=get_host())
def resolve_gnd(path):
    """Resolve GND records."""
    return resolve_record(path, AgentGndRecord)
