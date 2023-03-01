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

import requests
from celery import shared_task
from flask import current_app
from pymarc.marcxml import parse_xml_to_array
from sickle import Sickle
from six import BytesIO

from .api import AgentGndRecord
from ...marctojson.do_gnd_agent import Transformation
from ...utils import MyOAIItemIterator, oai_process_records_from_dates, \
    oai_save_records_from_dates, requests_retry_session


@shared_task
def process_records_from_dates(from_date=None, until_date=None,
                               ignore_deleted=False, dbcommit=True,
                               reindex=True, test_md5=True, verbose=False,
                               debug=False, viaf_online=False, **kwargs):
    """Harvest multiple records from an OAI repo.

    :param name: The name of the OAIHarvestConfig to use instead of passing
                 specific parameters.
    :param from_date: The lower bound date for the harvesting (optional).
    :param until_date: The upper bound date for the harvesting (optional).
    """
    return oai_process_records_from_dates(
        name='agents.gnd',
        sickle=Sickle,
        max_retries=current_app.config.get('RERO_OAI_RETRIES', 0),
        oai_item_iterator=MyOAIItemIterator,
        transformation=Transformation,
        access_token=current_app.config.get('RERO_OAI_GND_TOKEN'),
        record_class=AgentGndRecord,
        days_spann=4,
        from_date=from_date,
        until_date=until_date,
        ignore_deleted=ignore_deleted,
        dbcommit=dbcommit,
        reindex=reindex,
        test_md5=test_md5,
        verbose=verbose,
        debug=debug,
        viaf_onle=viaf_online,
        kwargs=kwargs
    )


@shared_task
def save_records_from_dates(file_name, from_date=None, until_date=None,
                            verbose=False):
    """Harvest and save multiple records from an OAI repo.

    :param name: The name of the OAIHarvestConfig to use instead of passing
                 specific parameters.
    :param from_date: The lower bound date for the harvesting (optional).
    :param until_date: The upper bound date for the harvesting (optional).
    """
    # data on IDREF Servers starts on 2000-10-01
    return oai_save_records_from_dates(
        name='agents.gnd',
        file_name=file_name,
        sickle=Sickle,
        max_retries=current_app.config.get('RERO_OAI_RETRIES', 0),
        oai_item_iterator=MyOAIItemIterator,
        access_token=current_app.config.get('RERO_OAI_GND_TOKEN'),
        days_spann=30,
        from_date=from_date,
        until_date=until_date,
        verbose=verbose
    )


@shared_task
def gnd_get_record(id, debug=False):
    """Get a record from GND SRU repo.

    GND documentation:
    https://www.dnb.de/DE/Service/Hilfe/Katalog/kataloghilfe.html?nn=587750#link
    https://services.dnb.de/sru/authorities?version=1.1
    &operation=searchRetrieve&query=idn%3D007355440&recordSchema=MARC21-xml
    """
    url = current_app.config.get(
        'RERO_MEF_AGENTS_GND_GET_RECORD').replace('{id}', id)
    trans_record = None
    msg = f'SRU-agents.gnd  get: {id:<15} {url}'
    try:
        response = requests_retry_session().get(url)
        status_code = response.status_code
        if status_code == requests.codes.ok:
            if records := parse_xml_to_array(BytesIO(response.content)):
                trans_record = Transformation(records[0]).json
                msg = f'{msg} | OK'
            else:
                msg = f'{msg} | No record'
        else:
            msg = f'{msg} | HTTP Error: {status_code}'
    except Exception as err:
        msg = f'{msg} | Error: {err}'
        if debug:
            raise
    return trans_record, msg
