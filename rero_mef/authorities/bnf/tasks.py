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

from .api import BnfRecord
from ..marctojson.do_bnf_auth_person import Transformation
from ..mef.models import MefAction
from ..models import AgencyAction


@shared_task
def bnf_get_record(id, dbcommit=False, reindex=False, test_md5=False,
                   verbose=False, debug=False, **kwargs):
    """Get a record from BNF SRU repo.

    BNF documentation SRU:
    https://www.bnf.fr/sites/default/files/2019-04/service_sru_bnf.pdf
    """
    # http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=aut.recordid%20all%20%22FRBNF102979790%22
    base_url = 'http://catalogue.bnf.fr/api/'
    sru_search = 'SRU?version=1.2&operation=searchRetrieve'
    query_id = '&query=aut.recordid all "{id}"'.format(id=id)
    format = '&recordSchema=unimarcXchange'
    url = '{base_url}{sru_search}{query_id}{format}'.format(
        base_url=base_url,
        sru_search=sru_search,
        query_id=query_id,
        format=format
    )
    new_rec = None
    action = AgencyAction.DISCARD
    mef_action = MefAction.DISCARD
    response = requests.get(url)
    if response.status_code == requests.codes.ok:
        records = parse_xml_to_array(BytesIO(response.content))
        if records:
            rec = Transformation(records[0]).json
            try:
                new_rec, action, mef_action = BnfRecord.create_or_update(
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
                    'SRU-bnf get: {id} action: {action} {mef}'.format(
                        id=id,
                        action=action,
                        mef=mef_action
                    )
                )
    return new_rec, action, mef_action
