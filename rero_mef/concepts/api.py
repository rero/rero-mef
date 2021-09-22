# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2020 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""API for manipulating records."""

from flask import current_app
from invenio_search import current_search

from ..api import ReroIndexer, ReroMefRecord


class ConceptRecord(ReroMefRecord):
    """Authority Record class."""

    name = None
    concept = None

    def __init__(self, *args, **kwargs):
        """Init class."""
        super().__init__(*args, **kwargs)
        self.concept = self.name

    @classmethod
    def update_indexes(cls):
        """Update indexes."""
        try:
            index = 'fconcepts_{cls.concept}'
            current_search.flush_and_refresh(index=index)
        except Exception as err:
            current_app.logger.error(f'ERROR flush and refresh: {err}')


class ConceptIndexer(ReroIndexer):
    """Indexing class for agents."""
