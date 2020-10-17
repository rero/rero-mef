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

from celery import shared_task
from flask import current_app
from sickle import Sickle

from .api import GndRecord
from ..marctojson.do_gnd_contribution import Transformation
from ...utils import MyOAIItemIterator, oai_get_record, \
    oai_process_records_from_dates, oai_save_records_from_dates


@shared_task
def process_records_from_dates(from_date=None, until_date=None,
                               ignore_deleted=False, dbcommit=True,
                               reindex=True, test_md5=True, verbose=False,
                               debug=False, **kwargs):
    """Harvest multiple records from an OAI repo.

    :param name: The name of the OAIHarvestConfig to use instead of passing
                 specific parameters.
    :param from_date: The lower bound date for the harvesting (optional).
    :param until_date: The upper bound date for the harvesting (optional).
    """
    return oai_process_records_from_dates(
        name='gnd',
        sickle=Sickle,
        max_retries=current_app.config.get('RERO_OAI_RETRIES', 0),
        oai_item_iterator=MyOAIItemIterator,
        transformation=Transformation,
        access_token=current_app.config.get('RERO_OAI_GND_TOKEN'),
        record_cls=GndRecord,
        days_spann=4,
        from_date=from_date,
        until_date=until_date,
        ignore_deleted=ignore_deleted,
        dbcommit=dbcommit,
        reindex=dbcommit,
        test_md5=test_md5,
        verbose=verbose,
        debug=debug,
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
        name='gnd',
        file_name=file_name,
        sickle=Sickle,
        max_retries=current_app.config.get('RERO_OAI_RETRIES', 0),
        oai_item_iterator=MyOAIItemIterator,
        days_spann=30,
        from_date=from_date,
        until_date=until_date,

    )


@shared_task
def gnd_get_record(id, verbose=False, debug=False):
    """Get a record from GND OAI repo."""
    return oai_get_record(
        id=id,
        name='gnd',
        transformation=Transformation,
        record_cls=GndRecord,
        access_token=current_app.config.get('RERO_OAI_GND_TOKEN'),
        identifier='oai:dnb.de/authorities/',
        verbose=verbose,
        debug=debug
    )
