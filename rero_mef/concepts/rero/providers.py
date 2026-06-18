# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Identifier provider."""

from invenio_pidstore.models import PIDStatus
from invenio_pidstore.providers.base import BaseProvider

from .models import ConceptReroIdentifier


class ConceptReroProvider(BaseProvider):
    """Concepts identifier provider."""

    pid_type = "corero"
    """Type of persistent identifier."""

    pid_identifier = ConceptReroIdentifier.__tablename__
    """Identifier for table name"""

    pid_provider = None
    """Provider name.

    The provider name is not recorded in the PID since the provider does not provide any additional features besides
    creation of Concept ids.
    """

    default_status = PIDStatus.REGISTERED
    """Concepts IDs are by default registered immediately."""
