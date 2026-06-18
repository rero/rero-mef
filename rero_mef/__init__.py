# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""RERO Multilingual Entity File (MEF) system.

This package provides a comprehensive framework for aggregating and managing bibliographic entities (agents, concepts,
and places) from multiple international authority files including VIAF, IdRef, GND, and RERO.

The MEF system creates unified records by linking entities across different authority sources, enabling multilingual
access and consistent referencing in library systems.

Main components:
- Entity record management (agents, concepts, places)
- Authority file integration (VIAF, IdRef, GND, RERO)
- MEF aggregation and indexing
- REST API for entity access and updates
- MARC21 to JSON conversion
"""

from .ext import REROMEFAPP
from .version import __version__ as __version__

__all__ = ("REROMEFAPP",)
