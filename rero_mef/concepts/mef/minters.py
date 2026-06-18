# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Identifier minters."""

from .providers import ConceptMefProvider


def mef_id_minter(
    record_uuid, data, provider=ConceptMefProvider, pid_key="pid", object_type="rec"
):
    """RERO ILS MEF concept pid minter."""
    assert pid_key not in data
    provider = provider.create(object_type=object_type, object_uuid=record_uuid)
    pid = provider.pid
    data[pid_key] = pid.pid_value

    return pid
