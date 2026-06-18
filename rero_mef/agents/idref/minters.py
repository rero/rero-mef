# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Identifier minters."""

from functools import partial

from ...minters import id_minter
from .providers import AgentIdrefProvider

idref_id_minter = partial(id_minter, provider=AgentIdrefProvider, recid_field="pid")
