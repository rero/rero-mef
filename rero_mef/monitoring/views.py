# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""REST API of the MEF monitoring, beside the shared monitoring of rero-invenio-base."""

from flask import Blueprint, jsonify
from rero_invenio_base.modules.monitoring.views import check_permission

from .api import Monitoring

api_blueprint = Blueprint("mef_monitoring", __name__, url_prefix="/monitoring")
api_blueprint.before_request(check_permission)


@api_blueprint.route("/mef_counts")
def mef_counts():
    """Display, for each source, the records in the database and in the MEF records.

    :return: jsonified counts of the MEF records and of the source records, and their difference.
    """
    return jsonify({"data": Monitoring().check_mef()})
