# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later


"""Json resolvers."""

import jsonresolver

from ....utils import get_host, resolve_record
from ..api import ConceptGndRecord


@jsonresolver.route("/api/concepts/gnd/<path:path>", host=get_host())
def resolve_gnd(path):
    """Resolve Concepts records."""
    return resolve_record(path, ConceptGndRecord)
