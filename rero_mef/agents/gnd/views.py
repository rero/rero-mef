# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2021 RERO
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

"""Agent GND views."""

from flask import Blueprint, redirect, request, url_for

api_blueprint = Blueprint(
    'api_agents_gnd',
    __name__,
    url_prefix='/gnd'
)


@api_blueprint.route('')
@api_blueprint.route('/')
def redirect_list():
    """Redirect list to new address."""
    return redirect(
        url_for('invenio_records_rest.aggnd_list', **request.args),
        code=308
    )


@api_blueprint.route('/<pid>')
def redirect_item(pid):
    """Redirect item to new address."""
    return redirect(
        url_for(
            'invenio_records_rest.aggnd_item', pid_value=pid, **request.args),
        code=308
    )
