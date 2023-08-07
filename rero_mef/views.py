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

from flask import Blueprint, Response, jsonify, request, stream_with_context

from .agents import AgentMefRecord
from .concepts import ConceptMefRecord
from .places import PlaceMefRecord

api_blueprint = Blueprint(
    'api_blueprint',
    __name__,
    url_prefix='/'
)


@api_blueprint.route('/agents/mef/latest/<pid_type>:<pid>')
def agent_mef_get_latest(pid_type, pid):
    """Get latest MEF for pid and type."""
    return jsonify(AgentMefRecord.get_latest(pid_type=pid_type, pid=pid))


@api_blueprint.route('/agents/mef/updated', methods=['POST'])
def agent_mef_get_updated():
    """Get latest MEF for pid and type."""
    data = request.get_json()
    generate = AgentMefRecord.get_updated(data)
    return Response(
        stream_with_context(generate), content_type='application/json'
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


@api_blueprint.route('/places/mef/latest/<pid_type>:<pid>')
def place_mef_get_latest(pid_type, pid):
    """Get latest MEF for pid and type."""
    return jsonify(PlaceMefRecord.get_latest(pid_type=pid_type, pid=pid))


@api_blueprint.route('/places/mef/updated', methods=['POST'])
def place_mef_get_updated():
    """Get latest MEF for pid and type."""
    data = request.get_json()
    generate = PlaceMefRecord.get_updated(data)
    return Response(
        stream_with_context(generate), content_type='application/json'
    )
