# -*- coding: utf-8 -*-
#
# This file is part of RERO MEF.
# Copyright (C) 2018 RERO.
#
# RERO MEF is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO MEF is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO MEF; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Tasks used by  RERO-MEF."""

import traceback

import click
import requests
from celery import shared_task
from jsonschema.exceptions import ValidationError
from pymarc.marcxml import parse_xml_to_array
from six import BytesIO

from .api import ReroRecord
from ..marctojson.do_rero_auth_person import Transformation
from ..mef.models import MefAction
from ..models import AgencyAction


@shared_task
def rero_get_record(id, dbcommit=False, reindex=False, test_md5=False,
                    verbose=False, debug=False, **kwargs):
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
    new_rec = None
    action = AgencyAction.DISCARD
    mef_action = MefAction.DISCARD
    response = requests.get(url)
    if response.status_code == requests.codes.ok:
        try:
            records = parse_xml_to_array(BytesIO(response.content))
            if records:
                rec = Transformation(records[0]).json
                try:
                    new_rec, action, mef_action = ReroRecord.create_or_update(
                        rec,
                        dbcommit=dbcommit,
                        reindex=reindex,
                        test_md5=test_md5
                    )
                except ValidationError:
                    new_rec = None,
                    action = AgencyAction.VALIDATIONERROR
                    mef_action = MefAction.DISCARD
                    if debug:
                        traceback.print_exc()
                except Exception:
                    new_rec = None,
                    action = AgencyAction.ERROR
                    mef_action = MefAction.DISCARD
                    if debug:
                        traceback.print_exc()
                if verbose:
                    click.echo(
                        'DATA-rero get: {id} action: {action} {mef}'.format(
                            id=id,
                            action=action,
                            mef=mef_action
                        )
                    )
        except Exception:
            pass
    return new_rec, action, mef_action
