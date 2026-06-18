# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later


"""Json resolvers."""

import jsonresolver

from ....utils import get_host, resolve_record
from ..api import PlaceGndRecord


@jsonresolver.route("/api/places/gnd/<path:path>", host=get_host())
def resolve_gnd(path):
    """Resolve Places records."""
    return resolve_record(path, PlaceGndRecord)
