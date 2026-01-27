# RERO MEF
# Copyright (C) 2020 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

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
