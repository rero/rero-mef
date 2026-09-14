# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test that a record refused by its schema leaves nothing behind.

The pid is minted before the record is validated, and `Record.create` validates
inside a savepoint of its own. A refused record used to roll back its own row
and keep the pid, which then answered to nothing and blocked every later attempt
to create the record under it.
"""

from copy import deepcopy
from unittest.mock import patch

import pytest
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from jsonschema.exceptions import ValidationError

from rero_mef.api import Action, format_record_error
from rero_mef.concepts import ConceptGndRecord
from rero_mef.monitoring.api import Monitoring


def test_a_refused_record_mints_no_pid(app, concept_gnd_link_data):
    """A record its schema refuses leaves neither a record nor a pid."""
    data = deepcopy(concept_gnd_link_data)
    # `additionalProperties` is false on the common concept schema.
    data["not_a_concept_field"] = "refused by the schema"

    _, action = ConceptGndRecord.create_or_update(data=data, dbcommit=True, reindex=True)

    assert action == Action.ERROR
    assert ConceptGndRecord.get_record_by_pid(data["pid"]) is None
    with pytest.raises(PIDDoesNotExistError):
        PersistentIdentifier.get(ConceptGndRecord.provider.pid_type, data["pid"])
    assert Monitoring.get_dangling_pids(ConceptGndRecord.provider.pid_type) == []


def test_a_refused_record_is_logged_with_its_reason(app, concept_gnd_link_data):
    """The error names the entity, the pid and the field that was refused."""
    data = deepcopy(concept_gnd_link_data)
    data["type"] = "bf:Person"  # not in the concept `type` enum

    # Asserting on the logger itself: a CLI group run earlier in the session turns off its propagation, so `caplog`
    # cannot be relied on to see this. See `ensure_single_stream_handler`.
    with patch.object(app.logger, "error") as logged:
        ConceptGndRecord.create_or_update(data=data, dbcommit=True, reindex=True)

    logged.assert_called_once()
    message = logged.call_args.args[0]
    assert message.startswith(f"CREATE {ConceptGndRecord.name} {data['pid']}: ValidationError type:")
    # The whole schema and instance stay out of the log.
    assert len(message.splitlines()) == 1


def test_the_session_stays_usable_after_a_refused_record(app, concept_gnd_link_data):
    """Rolling back to the savepoint leaves the outer transaction alive."""
    refused = deepcopy(concept_gnd_link_data)
    refused["pid"] = "refused"
    refused["not_a_concept_field"] = "refused by the schema"
    _, action = ConceptGndRecord.create_or_update(data=refused, dbcommit=True, reindex=True)
    assert action == Action.ERROR

    record, action = ConceptGndRecord.create_or_update(data=concept_gnd_link_data, dbcommit=True, reindex=True)
    assert action == Action.CREATE
    assert ConceptGndRecord.get_record_by_pid(record.pid)


def test_format_record_error_keeps_one_line():
    """A validation error is reduced to its message and the field it points at."""
    error = ValidationError("'bf:Person' is not one of ['bf:Topic', 'bf:Temporal']", path=["type"])
    assert format_record_error(error) == "ValidationError type: 'bf:Person' is not one of ['bf:Topic', 'bf:Temporal']"

    assert format_record_error(ValidationError("'pid' is a required property")) == (
        "ValidationError /: 'pid' is a required property"
    )

    assert format_record_error(ValueError("boom")) == "ValueError: boom"
