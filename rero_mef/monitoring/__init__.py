# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""System monitoring and health check functionality.

This module provides tools for monitoring the health and status of the RERO MEF system, including database connectivity,
Search status, and service availability checks.

Main components:
- Monitoring: Health check and system status monitoring
"""

from .api import Monitoring

__all__ = ("Monitoring",)
