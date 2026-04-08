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

"""Persistent identifier minters."""


def id_minter(
    record_uuid, data, provider, pid_key="pid", object_type="rec", recid_field=""
):
    """Mint a persistent identifier for a record.

    Creates a new persistent identifier and assigns it to the record data. The PID value is extracted from the specified
    field in the record data.

    :param record_uuid: UUID of the record to mint the PID for.
    :param data: Dictionary containing the record data.
    :param provider: PID provider class to use for creating the identifier.
    :param pid_key: Key in data where the PID value will be stored (default: 'pid').
    :param object_type: Type of object being identified (default: 'rec').
    :param recid_field: Field in data containing the PID value to use.
    :returns: The newly created persistent identifier.
    :raises AssertionError: If recid_field is not present in data.
    """
    # assert pid_key not in data
    assert recid_field in data
    pid_value = data[recid_field]
    provider = provider.create(
        object_type=object_type, object_uuid=record_uuid, pid_value=pid_value
    )
    pid = provider.pid
    data[pid_key] = pid.pid_value
    return pid
