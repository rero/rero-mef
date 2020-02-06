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

import datetime
import time
from datetime import timedelta
from io import StringIO

import click
import requests
from celery import shared_task
from dateutil import parser
from flask import current_app
from invenio_db import db
from invenio_oaiharvester.api import get_info_by_oai_name
from invenio_oaiharvester.errors import WrongDateCombination
from invenio_oaiharvester.utils import get_oaiharvest_object
from pymarc.marcxml import parse_xml_to_array
from sickle import OAIResponse, Sickle, oaiexceptions
from sickle.iterator import OAIItemIterator
from sickle.oaiexceptions import NoRecordsMatch

from .api import IdrefRecord
from ..marctojson.do_idref_auth_person import Transformation
from ..tasks import get_record


class MyOAIItemIterator(OAIItemIterator):
    """OAI item iterator with more robuste complete response test."""

    def _next_response(self):
        """Get the next response from the OAI server."""
        params = self.params
        if self.resumption_token:
            params = {
                'resumptionToken': self.resumption_token.token,
                'verb': self.verb
            }
        self.oai_response = self.sickle.harvest(**params)
        error = self.oai_response.xml.find(
            './/' + self.sickle.oai_namespace + 'error')
        if error is not None:
            code = error.attrib.get('code', 'UNKNOWN')
            description = error.text or ''
            try:
                raise getattr(
                    oaiexceptions, code[0].upper() + code[1:])(description)
            except AttributeError:
                raise oaiexceptions.OAIError(description)
        if self.resumption_token:
            # Test we got a complete response ('resumptionToken' in xml)
            resumption_token_element = self.oai_response.xml.find(
                './/' + self.sickle.oai_namespace + 'resumptionToken')

            if resumption_token_element is None:
                msg = ('ERROR HARVESTING incomplete response:'
                       '{cursor} {token}').format(
                    cursor=self.resumption_token.cursor,
                    token=self.resumption_token.token
                )
                current_app.logger.error(msg)
            else:
                self.resumption_token = self._get_resumption_token()

                self._items = self.oai_response.xml.iterfind(
                    './/' + self.sickle.oai_namespace + self.element)

        else:
            # first time
            self.resumption_token = self._get_resumption_token()

            self._items = self.oai_response.xml.iterfind(
                './/' + self.sickle.oai_namespace + self.element)


class MySickle(Sickle):
    """Sickle class for OAI harvesting."""

    def harvest(self, **kwargs):  # pragma: no cover
        """Make HTTP requests to the OAI server.

        :param kwargs: OAI HTTP parameters.
        :rtype: :class:`sickle.OAIResponse`
        """
        for _ in range(self.max_retries):
            if self.http_method == 'GET':
                http_response = requests.get(self.endpoint, params=kwargs,
                                             **self.request_args)
            else:
                http_response = requests.post(self.endpoint, data=kwargs,
                                              **self.request_args)
            if http_response.status_code == 503:
                try:
                    retry_after = int(http_response.headers.get('retry-after'))
                except TypeError:
                    retry_after = 30
                current_app.logger.warning(
                    'HTTP 503! Retrying after {retry} seconds...'.format(
                        retry=retry_after
                    )
                )
                time.sleep(retry_after)
            else:
                http_response.raise_for_status()
                if self.encoding:
                    http_response.encoding = self.encoding
                return OAIResponse(http_response, params=kwargs)


@shared_task
def process_records_from_dates(from_date=None, until_date=None,
                               ignore_deleted=False, dbcommit=True,
                               reindex=True, test_md5=True,
                               verbose=False, **kwargs):
    """Harvest multiple records from an OAI repo.

    :param name: The name of the OAIHarvestConfig to use instead of passing
                 specific parameters.
    :param from_date: The lower bound date for the harvesting (optional).
    :param until_date: The upper bound date for the harvesting (optional).
    """
    # data on IDREF Servers starts on 2000-10-01
    name = 'idref'
    days_spann = 30
    lastrun = None
    url, metadata_prefix, lastrun, setspecs = get_info_by_oai_name(name)

    request = MySickle(url, iterator=MyOAIItemIterator)

    dates = {
        'from': from_date or lastrun,
        'until': until_date
    }

    # Sanity check
    if (dates['until'] is not None) and (dates['from'] > dates['until']):
        raise WrongDateCombination("'Until' date larger than 'from' date.")

    lastrun_date = datetime.datetime.now()

    setspecs = setspecs.split() or [None]
    count = 0
    action_count = {}
    mef_action_count = {}
    for spec in setspecs:
        params = {
            'metadataPrefix': metadata_prefix or "marc-xml",
            'ignore_deleted': ignore_deleted
        }
        params.update(dates)
        if spec:
            params['set'] = spec

        my_from_date = parser.parse(dates['from'])
        my_until_date = lastrun_date
        if dates['until']:
            my_until_date = parser.parse(dates['until'])
        while my_from_date <= my_until_date:
            until_date = my_from_date + timedelta(days=days_spann)
            if until_date > my_until_date:
                until_date = my_until_date
            dates = {
                'from': my_from_date.strftime("%Y-%m-%d"),
                'until': until_date.strftime("%Y-%m-%d")
            }
            params.update(dates)

            try:
                for record in request.ListRecords(**params):
                    # Todo: DELETED
                    count += 1
                    records = parse_xml_to_array(StringIO(record.raw))
                    try:
                        try:
                            updated = datetime.datetime.strptime(
                                records[0]['005'].data,
                                '%Y%m%d%H%M%S.%f'
                            )
                        except:
                            updated = '????'
                        rec = Transformation(records[0]).json
                        pid = rec.get('pid')
                        rec, action, mef_action = IdrefRecord.create_or_update(
                            rec,
                            dbcommit=dbcommit,
                            reindex=reindex,
                            test_md5=test_md5
                        )
                        count_a = action_count.setdefault(action, 0)
                        action_count[action] = count_a + 1
                        count_a = mef_action_count.setdefault(mef_action, 0)
                        mef_action_count[mef_action] = count_a + 1
                        if verbose:
                            click.echo(
                                ('OAI-IDREF: {pid} updated: {updated}'
                                 ' action: {action} {mef}').format(
                                    pid=pid,
                                    action=action,
                                    mef=mef_action,
                                    updated=updated
                                )
                            )
                    except Exception as err:
                        msg = 'ERROR creating {name} {count}: {err}\n{rec}'
                        msg = msg.format(
                            name=name,
                            count=count,
                            err=err,
                            rec=rec
                        )
                        current_app.logger.error(msg)
                        # import traceback
                        # traceback.print_exc()
            except NoRecordsMatch:
                my_from_date = my_from_date + timedelta(days=(days_spann + 1))
                continue
            except Exception as err:
                current_app.logger.error(err)
                count = -1

            my_from_date = my_from_date + timedelta(days=(days_spann + 1))
            if verbose:
                click.echo(
                    ('OAI-IDREF: {from_d} .. +{days_spann}').format(
                        from_d=my_from_date.strftime("%Y-%m-%d"),
                        days_spann=days_spann
                    )
                )

    # Update lastrun?
    if from_date is None and until_date is None and name is not None:
        oai_source = get_oaiharvest_object(name)
        oai_source.update_lastrun(lastrun_date)
        oai_source.save()
        db.session.commit()
    return count, action_count, mef_action_count


@shared_task
def idref_get_record(id, dbcommit=False, reindex=False, test_md5=False,
                     verbose=False, **kwargs):
    """Get a record from GND OAI repo."""
    identifier = 'oai:IdRefOAIServer.fr:'
    return get_record(id, name='gnd', transformation=Transformation,
                      record_class=IdrefRecord, identifier=identifier,
                      dbcommit=dbcommit, reindex=reindex, test_md5=test_md5,
                      verbose=verbose, kwargs=kwargs)
