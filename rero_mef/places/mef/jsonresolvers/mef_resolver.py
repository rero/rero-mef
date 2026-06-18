# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later


"""Json resolvers."""

import jsonresolver

from ....utils import get_host, resolve_record
from ..api import PlaceMefRecord


@jsonresolver.route("/api/places/mef/<path:path>", host=get_host())
def resolve_mef(path):
    """Resolve Mef records."""
    return resolve_record(path, PlaceMefRecord)
