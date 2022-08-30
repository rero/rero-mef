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

from flask import Blueprint, Response, jsonify, redirect, request, \
    stream_with_context, url_for

from .agents import AgentMefRecord
from .concepts import ConceptMefRecord

api_blueprint = Blueprint(
    'api_blueprint',
    __name__,
    url_prefix='/'
)


@api_blueprint.route('/mef')
@api_blueprint.route('/mef/')
def agent_mef_redirect_list():
    """Redirect list to new address."""
    return redirect(
        url_for('invenio_records_rest.mef_list', **request.args),
        code=308
    )


@api_blueprint.route('/mef/<pid>')
def agent_mef_redirect_item(pid):
    """Redirect item to new address."""
    return redirect(
        url_for(
            'invenio_records_rest.mef_item', pid_value=pid, **request.args),
        code=308
    )


@api_blueprint.route('/mef/latest/<pid_type>:<pid>')
@api_blueprint.route('/agents/mef/latest/<pid_type>:<pid>')
def agent_mef_get_latest(pid_type, pid):
    """Get latest MEF for pid and type."""
    return jsonify(AgentMefRecord.get_latest(pid_type=pid_type, pid=pid))


@api_blueprint.route('/mef/updated', methods=['POST'])
@api_blueprint.route('/agents/mef/updated', methods=['POST'])
def agent_mef_get_updated():
    """Get latest MEF for pid and type."""
    data = request.get_json()
    generate = AgentMefRecord.get_updated(data)
    return Response(
        stream_with_context(generate), content_type='application/json'
    )


@api_blueprint.route('/gnd')
@api_blueprint.route('/gnd/')
def agent_gnd_redirect_list():
    """Redirect list to new address."""
    return redirect(
        url_for('invenio_records_rest.aggnd_list', **request.args),
        code=308
    )


@api_blueprint.route('/gnd/<pid>')
def agent_gnd_redirect_item(pid):
    """Redirect item to new address."""
    return redirect(
        url_for(
            'invenio_records_rest.aggnd_item', pid_value=pid, **request.args),
        code=308
    )


@api_blueprint.route('/idref')
@api_blueprint.route('/idref/')
def agent_idref_redirect_list():
    """Redirect list to new address."""
    return redirect(
        url_for('invenio_records_rest.aidref_list', **request.args),
        code=308
    )


@api_blueprint.route('/idref(<pid>')
def agent_idref_redirect_item(pid):
    """Redirect item to new address."""
    return redirect(
        url_for(
            'invenio_records_rest.aidref_item', pid_value=pid, **request.args),
        code=308
    )


@api_blueprint.route('/rero')
@api_blueprint.route('/rero/')
def agent_rero_redirect_list():
    """Redirect list to new address."""
    return redirect(
        url_for('invenio_records_rest.agrero_list', **request.args),
        code=308
    )


@api_blueprint.route('/rero/<pid>')
def agent_rero_redirect_item(pid):
    """Redirect item to new address."""
    return redirect(
        url_for(
            'invenio_records_rest.agrero_item', pid_value=pid, **request.args),
        code=308
    )


@api_blueprint.route('/viaf')
@api_blueprint.route('/viaf/')
def agent_viaf_redirect_list():
    """Redirect list to new address."""
    return redirect(
        url_for('invenio_records_rest.viaf_list', **request.args),
        code=308
    )


@api_blueprint.route('/viaf/<pid>')
def agent_viaf_redirect_item(pid):
    """Redirect item to new address."""
    return redirect(
        url_for(
            'invenio_records_rest.viaf_item', pid_value=pid, **request.args),
        code=308
    )


@api_blueprint.route('/concepts/mef/latest/<pid_type>:<pid>')
def concept_mef_get_latest(pid_type, pid):
    """Get latest MEF for pid and type."""
    return jsonify(ConceptMefRecord.get_latest(pid_type=pid_type, pid=pid))


@api_blueprint.route('/concepts/mef/updated', methods=['POST'])
def concept_mef_get_updated():
    """Get latest MEF for pid and type."""
    data = request.get_json()
    generate = ConceptMefRecord.get_updated(data)
    return Response(
        stream_with_context(generate), content_type='application/json'
    )
