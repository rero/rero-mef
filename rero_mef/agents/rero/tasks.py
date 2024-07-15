# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2024 RERO
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

"""Tasks used by  RERO-MEF."""

import requests
from celery import shared_task
from flask import current_app
from pymarc.marcxml import parse_xml_to_array
from six import BytesIO

from ...marctojson.do_rero_agent import Transformation
from ...utils import requests_retry_session


@shared_task
def rero_get_record(id_, debug=False):
    """Get a record from RERO data repo.

    RERO documentation:
    http://data.rero.ch/
    http://data.rero.ch/02-A000069866/marcxml
    """
    url = current_app.config["RERO_MEF_AGENTS_RERO_GET_RECORD"].replace("{id}", id_)
    msg = f"API-agents.rero  get: {id:<15} {url}"
    try:
        response = requests_retry_session().get(url)
        status_code = response.status_code
        if status_code == requests.codes.ok:
            if records := parse_xml_to_array(BytesIO(response.content)):
                trans_record = Transformation(records[0]).json
                pid = trans_record.get("pid")
                if id_ != pid:
                    return None, f"{msg} | PID changed: {id_} -> {pid}"
                return trans_record, f"{msg} | OK"
            return None, f"{msg} | No record"
        return None, f"{msg} | HTTP Error: {status_code}"
    except Exception as err:
        if debug:
            raise
        return None, f"{msg} | Error: {err}"
