# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Invenio record extensions for RERO MEF."""

from .deleted import DeletedStateExtension
from .md5 import MD5Extension
from .schema import SchemaExtension

__all__ = ["DeletedStateExtension", "MD5Extension", "SchemaExtension"]
