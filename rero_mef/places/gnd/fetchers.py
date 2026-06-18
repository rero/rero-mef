# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Persistent identifier fetchers."""

from functools import partial

from ...fetchers import id_fetcher
from .providers import PlaceGndProvider

gnd_id_fetcher = partial(id_fetcher, provider=PlaceGndProvider)
