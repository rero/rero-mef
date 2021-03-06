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

"""Tasks used by  RERO-MEF."""

import click
import requests
from celery import shared_task
from pymarc.marcxml import parse_xml_to_array
from six import BytesIO

from ...marctojson.do_rero_agent import Transformation


@shared_task
def rero_get_record(id, verbose=False, debug=False):
    """Get a record from RERO data repo.

    RERO documentation:
    http://data.rero.ch/
    http://data.rero.ch/02-A000069866/marcxml
    """
    base_url = 'http://data.rero.ch/02-'
    query_id = '{id}'.format(id=id)
    format = '/marcxml'
    url = '{base_url}{query_id}{format}'.format(
        base_url=base_url,
        query_id=query_id,
        format=format
    )
    trans_record = None
    response = requests.get(url)
    if response.status_code == requests.codes.ok:
        try:
            records = parse_xml_to_array(BytesIO(response.content))
            if records:
                trans_record = Transformation(records[0]).json
                if verbose:
                    click.echo('API-rero get: {id}'.format(id=id))
        except Exception as err:
            if verbose:
                click.echo('ERROR get rero record: {err}'.format(err=err))
            if debug:
                raise(err)
    return trans_record
