# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Identifier provider."""

from invenio_pidstore.models import PIDStatus
from invenio_pidstore.providers.base import BaseProvider

from ...models import MefIdentifier


class MefProvider(BaseProvider):
    """Mef identifier provider."""

    pid_type = "mef"
    """Type of persistent identifier."""

    pid_identifier = MefIdentifier.__tablename__
    """Identifier for table name"""

    pid_provider = None
    """Provider name.

    The provider name is not recorded in the PID since the provider does not provide any additional features besides
    creation of Document ids.
    """

    default_status = PIDStatus.REGISTERED
    """Mef IDs are by default registered immediately."""

    @classmethod
    def create(cls, object_type=None, object_uuid=None, **kwargs):
        """Create a new MEF agent identifier."""
        assert "pid_value" not in kwargs
        kwargs["pid_value"] = str(MefIdentifier.next())
        kwargs.setdefault("status", cls.default_status)
        if object_type and object_uuid:
            kwargs["status"] = PIDStatus.REGISTERED
        return super().create(
            object_type=object_type, object_uuid=object_uuid, **kwargs
        )
