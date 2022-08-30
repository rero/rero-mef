# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2022 RERO
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

"""Agent MEF views."""

from flask import Blueprint, jsonify, redirect, request, url_for

from .agents import AgentMefRecord

api_blueprint = Blueprint(
    'api_blueprint',
    __name__,
    url_prefix='/'
)


@api_blueprint.route('/mef')
@api_blueprint.route('/mef/')
def redirect_list_mef():
    """Redirect list to new address."""
    return redirect(
        url_for('invenio_records_rest.mef_list', **request.args),
        code=308
    )


@api_blueprint.route('/mef/<pid>')
def redirect_item_mef(pid):
    """Redirect item to new address."""
    return redirect(
        url_for(
            'invenio_records_rest.mef_item', pid_value=pid, **request.args),
        code=308
    )


@api_blueprint.route('/mef/latest/<pid_type>:<pid>')
@api_blueprint.route('/agents/mef/latest/<pid_type>:<pid>')
def get_latest_mef(pid_type, pid):
    """Get latest MEF for pid and type."""
    return jsonify(AgentMefRecord.get_latest(pid_type=pid_type, pid=pid))


@api_blueprint.route('/gnd')
@api_blueprint.route('/gnd/')
def redirect_list_gnd():
    """Redirect list to new address."""
    return redirect(
        url_for('invenio_records_rest.aggnd_list', **request.args),
        code=308
    )


@api_blueprint.route('/gnd/<pid>')
def redirect_item_gnd(pid):
    """Redirect item to new address."""
    return redirect(
        url_for(
            'invenio_records_rest.aggnd_item', pid_value=pid, **request.args),
        code=308
    )


@api_blueprint.route('/idref')
@api_blueprint.route('/idref/')
def redirect_list_idref():
    """Redirect list to new address."""
    return redirect(
        url_for('invenio_records_rest.aidref_list', **request.args),
        code=308
    )


@api_blueprint.route('/idref(<pid>')
def redirect_item_idref(pid):
    """Redirect item to new address."""
    return redirect(
        url_for(
            'invenio_records_rest.aidref_item', pid_value=pid, **request.args),
        code=308
    )


@api_blueprint.route('/rero')
@api_blueprint.route('/rero/')
def redirect_list_rero():
    """Redirect list to new address."""
    return redirect(
        url_for('invenio_records_rest.agrero_list', **request.args),
        code=308
    )


@api_blueprint.route('/rero/<pid>')
def redirect_item_rero(pid):
    """Redirect item to new address."""
    return redirect(
        url_for(
            'invenio_records_rest.agrero_item', pid_value=pid, **request.args),
        code=308
    )


@api_blueprint.route('/viaf')
@api_blueprint.route('/viaf/')
def redirect_list_viaf():
    """Redirect list to new address."""
    return redirect(
        url_for('invenio_records_rest.viaf_list', **request.args),
        code=308
    )


@api_blueprint.route('/viaf/<pid>')
def redirect_item_viaf(pid):
    """Redirect item to new address."""
    return redirect(
        url_for(
            'invenio_records_rest.viaf_item', pid_value=pid, **request.args),
        code=308
    )
