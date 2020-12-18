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


"""Blueprint used for loading templates."""

from __future__ import absolute_import, print_function

from flask import Blueprint, render_template

from ..version import __version__

blueprint = Blueprint(
    'rero_mef',
    __name__,
    template_folder='templates',
    static_folder='static',
)

api_blueprint = Blueprint(
    'api_rero_mef',
    __name__
)


@blueprint.route('/')
def index():
    """Home Page."""
    return render_template('rero_mef/frontpage.html', version=__version__)
