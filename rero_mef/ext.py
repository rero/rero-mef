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

"""RERO MEF invenio module declaration."""

from __future__ import absolute_import, print_function

from invenio_indexer.signals import before_record_index

from .mef.listner import enrich_mef_data


class REROMEFAPP(object):
    """rero-mef extension."""

    def __init__(self, app=None):
        """RERO MEF App module."""
        if app:
            self.init_app(app)
            self.register_signals(app)

    def init_app(self, app):
        """Flask application initialization."""
        app.extensions['rero-mef'] = self

    def register_signals(self, app):
        """Register signals."""
        before_record_index.connect(enrich_mef_data, sender=app)
