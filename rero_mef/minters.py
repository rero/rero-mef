# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

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
