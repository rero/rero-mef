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

import time

from celery import shared_task
from flask import current_app
from sickle import OAIResponse, Sickle

from .api import AgentIdrefRecord
from ...marctojson.do_idref_agent import Transformation
from ...utils import MyOAIItemIterator, oai_get_record, \
    oai_process_records_from_dates, oai_save_records_from_dates


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
                    f'HTTP {http_response.status_code}! '
                    f'Retrying after {retry_after} seconds...'
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
                               verbose=False, debug=False, viaf_online=False,
                               **kwargs):
    """Harvest multiple records from an OAI repo.

    :param name: The name of the OAIHarvestConfig to use instead of passing
                 specific parameters.
    :param from_date: The lower bound date for the harvesting (optional).
    :param until_date: The upper bound date for the harvesting (optional).
    """
    # data on IDREF Servers starts on 2000-10-01
    return oai_process_records_from_dates(
        name='agents.idref',
        sickle=MySickle,
        max_retries=current_app.config.get('RERO_OAI_RETRIES', 0),
        oai_item_iterator=MyOAIItemIterator,
        transformation=Transformation,
        record_class=AgentIdrefRecord,
        days_spann=30,
        from_date=from_date,
        until_date=until_date,
        ignore_deleted=ignore_deleted,
        dbcommit=dbcommit,
        reindex=reindex,
        test_md5=test_md5,
        verbose=verbose,
        debug=debug,
        viaf_online=viaf_online,
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
        name='agents.idref',
        file_name=file_name,
        sickle=MySickle,
        max_retries=current_app.config.get('RERO_OAI_RETRIES', 0),
        oai_item_iterator=MyOAIItemIterator,
        days_spann=30,
        from_date=from_date,
        until_date=until_date,
        verbose=verbose
    )


@shared_task
def idref_get_record(id, verbose=False, debug=False):
    """Get a record from GND OAI repo."""
    return oai_get_record(
        id=id,
        name='agents.idref',
        transformation=Transformation,
        identifier='oai:IdRefOAIServer.fr:',
        debug=debug
    )
