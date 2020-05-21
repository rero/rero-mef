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

import time

from celery import shared_task
from flask import current_app
from sickle import OAIResponse, Sickle

from .api import IdrefRecord
from ..marctojson.do_idref_auth_person import Transformation
from ...utils import MyOAIItemIterator, oai_get_record, \
    oai_process_records_from_dates


class MySickle(Sickle):
    """Sickle class for OAI harvesting."""

    def harvest(self, **kwargs):  # pragma: no cover
        """Make HTTP requests to the OAI server.

        :param kwargs: OAI HTTP parameters.
        :rtype: :class:`sickle.OAIResponse`
        """
        http_response = self._request(kwargs)
        for _ in range(self.max_retries):
            if self._is_error_code(http_response.status_code) \
                    and http_response.status_code in self.retry_status_codes:
                retry_after = self.get_retry_after(http_response)
                current_app.logger.warning(
                    "HTTP {code}! Retrying after {after} seconds...".format(
                        code=http_response.status_code,
                        after=retry_after
                    )
                )
                time.sleep(retry_after)
                http_response = self._request(kwargs)
        http_response.raise_for_status()
        if self.encoding:
            http_response.encoding = self.encoding
        return OAIResponse(http_response, params=kwargs)


@shared_task
def process_records_from_dates(from_date=None, until_date=None,
                               ignore_deleted=False, dbcommit=True,
                               reindex=True, test_md5=True,
                               verbose=False, debug=False, **kwargs):
    """Harvest multiple records from an OAI repo.

    :param name: The name of the OAIHarvestConfig to use instead of passing
                 specific parameters.
    :param from_date: The lower bound date for the harvesting (optional).
    :param until_date: The upper bound date for the harvesting (optional).
    """
    # data on IDREF Servers starts on 2000-10-01
    return oai_process_records_from_dates(
        name='idref',
        sickle=MySickle,
        max_retries=current_app.config.get('RERO_OAI_RETRIES', 0),
        oai_item_iterator=MyOAIItemIterator,
        transformation=Transformation,
        record_cls=IdrefRecord,
        days_spann=30,
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
def idref_get_record(id, dbcommit=False, reindex=False, test_md5=False,
                     verbose=False, debug=False, **kwargs):
    """Get a record from GND OAI repo."""
    return oai_get_record(
        id=id,
        name='idref',
        transformation=Transformation,
        record_cls=IdrefRecord,
        identifier='oai:IdRefOAIServer.fr:',
        dbcommit=dbcommit,
        reindex=reindex,
        test_md5=test_md5,
        verbose=verbose,
        debug=debug,
        kwargs=kwargs
    )
