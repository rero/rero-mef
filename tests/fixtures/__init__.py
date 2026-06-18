# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test fixtures and mock data.

Provides pytest fixtures and sample data for testing agents, concepts,
and places across different authority sources.
"""

from pathlib import Path

from flask import current_app


class FixturesEngine:
    """Basic fixtures engine."""

    def run(self):
        """Run the fixtures loading."""
        dir_ = Path(__file__).parent
        app_data_folder = Path(current_app.instance_path) / "app_data"
        app_data_folder / "pages"
        dir_ / "data"
        dir_ / "pages"
