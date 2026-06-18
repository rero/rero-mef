# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Persistent identifier fetchers."""

from collections import namedtuple

#: Namedtuple holding a fetched persistent identifier (provider, pid_type, pid_value).
FetchedPID = namedtuple("FetchedPID", ["provider", "pid_type", "pid_value"])


def id_fetcher(_record_uuid, data, provider, pid_key="pid"):
    """Fetch a record's persistent identifier.

    :param _record_uuid: The record UUID (intentionally unused; present for
    API compatibility with invenio PID fetcher conventions).
    :param data: The record metadata.
    :param provider: The PID provider class.
    :param pid_key: Key in ``data`` holding the PID value (default: ``"pid"``).
    :returns: A :data:`rero_mef.fetchers.FetchedPID` instance.
    :raises KeyError: If ``pid_key`` is not present in ``data``.
    """
    return FetchedPID(
        provider=provider, pid_type=provider.pid_type, pid_value=data[pid_key]
    )
