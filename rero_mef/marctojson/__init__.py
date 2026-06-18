# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""MARC21 to JSON conversion utilities.

This module provides tools for converting MARC21 bibliographic records to JSON format for different authority sources
(IdRef, GND, RERO).

Main components:
- MARC21 record parsing
- Field-specific conversion handlers
- Authority-specific conversion rules (agents, concepts, places)
- Validation and error handling
- Logging utilities
"""
