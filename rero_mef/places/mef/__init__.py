# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Place MEF aggregated records.

This module provides the MEF (Multilingual Entity File) aggregation layer for place entities. MEF records combine and
link place records from multiple authority sources (IdRef, GND) into unified geographic entities.

The MEF record serves as the central hub that maintains relationships between equivalent place entities across different
authority files, enabling multilingual geographic access and consistent indexing.
"""
