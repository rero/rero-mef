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

# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 RERO.
#
# RERO Ebooks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Utilities."""

import datetime
import json
import traceback
from datetime import timedelta
from io import StringIO
from json import JSONDecodeError, JSONDecoder

import click
from dateutil import parser
from flask import current_app
from invenio_db import db
from invenio_oaiharvester.api import get_info_by_oai_name
from invenio_oaiharvester.errors import InvenioOAIHarvesterConfigNotFound, \
    WrongDateCombination
from invenio_oaiharvester.models import OAIHarvestConfig
from invenio_oaiharvester.utils import get_oaiharvest_object
from invenio_records_rest.utils import obj_or_import_string
from jsonschema.exceptions import ValidationError
from pymarc.marcxml import parse_xml_to_array
from sickle import Sickle, oaiexceptions
from sickle.iterator import OAIItemIterator
from sickle.oaiexceptions import NoRecordsMatch

from .contributions.mef.models import MefAction
from .contributions.models import AgencyAction


def add_oai_source(name, baseurl, metadataprefix='marc21',
                   setspecs='', comment='', update=False):
    """Add OAIHarvestConfig."""
    with current_app.app_context():
        source = OAIHarvestConfig.query.filter_by(name=name).first()
        if not source:
            source = OAIHarvestConfig(
                name=name,
                baseurl=baseurl,
                metadataprefix=metadataprefix,
                setspecs=setspecs,
                comment=comment
            )
            source.save()
            db.session.commit()
            return 'Added'
        elif update:
            source.name = name
            source.baseurl = baseurl
            source.metadataprefix = metadataprefix
            if setspecs != '':
                source.setspecs = setspecs
            if comment != '':
                source.comment = comment
            db.session.commit()
            return 'Updated'
        return 'Not Updated'


def oai_get_last_run(name, verbose=False):
    """Gets the lastrun for a OAI harvest configuration.

    :param name: name of the OAI harvest configuration.
    :return: datetime of last OAI harvest run.
    """
    try:
        oai_source = get_oaiharvest_object(name)
        lastrun_date = oai_source.lastrun
        if verbose:
            click.echo('OAI {name}: last run: {last_run}'.format(
                name=name,
                last_run=lastrun_date
            ))
        return lastrun_date
    except InvenioOAIHarvesterConfigNotFound:
        if verbose:
            click.echo(('ERROR OAI config not found: {name}').format(
                    name=name,
            ))
        return None


def oai_set_last_run(name, date, verbose=False):
    """Sets the lastrun for a OAI harvest configuration.

    :param name: name of the OAI harvest configuration.
    :param date: Date to set as last run
    :return: datetime of date to set.
    """
    try:
        oai_source = get_oaiharvest_object(name)
        lastrun_date = date
        if isinstance(date, str):
            lastrun_date = parser.parse(date)
        oai_source.update_lastrun(lastrun_date)
        oai_source.save()
        db.session.commit()
        if verbose:
            click.echo('OAI {name}: set last run: {last_run}'.format(
                name=name,
                last_run=lastrun_date
            ))
        return lastrun_date
    except InvenioOAIHarvesterConfigNotFound:
        if verbose:
            click.echo(('ERROR OAI config not found: {name}').format(
                name=name,
            ))
    except parser.ParserError as err:
        if verbose:
            click.echo(('OAI set lastrun {name}: {err}').format(
                name=name,
                err=err
            ))
    return None


class MyOAIItemIterator(OAIItemIterator):
    """OAI item iterator with accessToken."""

    def next_resumption_token_and_items(self):
        """Get next resumtion token and items."""
        self.resumption_token = self._get_resumption_token()
        self._items = self.oai_response.xml.iterfind(
            './/' + self.sickle.oai_namespace + self.element)

    def _next_response(self):
        """Get the next response from the OAI server."""
        params = self.params
        access_token = params.get('accessToken')
        if self.resumption_token:
            params = {
                'resumptionToken': self.resumption_token.token,
                'verb': self.verb
            }
        if access_token:
            params['accessToken'] = access_token

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
                self.next_resumption_token_and_items()
        else:
            # first time
            self.next_resumption_token_and_items()


def oai_process_records_from_dates(name, sickle, oai_item_iterator,
                                   transformation, record_cls, max_retries=0,
                                   access_token=None, days_spann=30,
                                   from_date=None, until_date=None,
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
    name = name
    days_spann = days_spann
    last_run = None
    url, metadata_prefix, last_run, setspecs = get_info_by_oai_name(name)

    request = sickle(url, iterator=oai_item_iterator, max_retries=max_retries)

    dates_inital = {
        'from': from_date or last_run,
        'until': until_date
    }
    update_last_run = from_date is None and until_date is None
    # Sanity check
    if dates_inital['until'] is not None \
            and dates_inital['from'] > dates_inital['until']:
        raise WrongDateCombination("'Until' date larger than 'from' date.")

    last_run_date = datetime.datetime.now()

    # If we don't have specifications for set searches the setspecs will be
    # set to e list with None to go into the retrieval loop without
    # a set definition (line 177)
    setspecs = setspecs.split() or [None]
    count = 0
    action_count = {}
    mef_action_count = {}
    for spec in setspecs:
        dates = dates_inital
        params = {
            'metadataPrefix': metadata_prefix,
            'ignore_deleted': ignore_deleted
        }
        if access_token:
            params['accessToken'] = access_token
        params.update(dates)
        if spec:
            params['set'] = spec

        my_from_date = parser.parse(dates['from'])
        my_until_date = last_run_date
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
                        rec = transformation(records[0]).json
                        pid = rec.get('pid')
                        rec, action, mef_action = record_cls.create_or_update(
                            rec,
                            dbcommit=dbcommit,
                            reindex=reindex,
                            test_md5=test_md5
                        )
                        action_count.setdefault(action.name, 0)
                        action_count[action.name] += 1
                        mef_action_count.setdefault(mef_action.name, 0)
                        mef_action_count[mef_action.name] += 1
                        if verbose:
                            click.echo(
                                ('OAI {name} {spec}: {pid} updated: {updated}'
                                 ' action: {action} {mef}').format(
                                    name=name,
                                    spec=spec,
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
                        if debug:
                            traceback.print_exc()
            except NoRecordsMatch:
                my_from_date = my_from_date + timedelta(days=days_spann + 1)
                continue
            except Exception as err:
                current_app.logger.error(err)
                if debug:
                    traceback.print_exc()
                count = -1

            my_from_date = my_from_date + timedelta(days=days_spann + 1)
            if verbose:
                click.echo(
                    ('OAI {name} {spec}: {from_d} .. +{days_spann}').format(
                        name=name,
                        spec=spec,
                        from_d=my_from_date.strftime("%Y-%m-%d"),
                        days_spann=days_spann
                    )
                )

    if update_last_run:
        if verbose:
            click.echo(
                ('OAI {name}: update last run: {last_run}').format(
                    name=name,
                    last_run=last_run_date
                )
            )
        oai_source = get_oaiharvest_object(name)
        oai_source.update_lastrun(last_run_date)
        oai_source.save()
        db.session.commit()
    return count, action_count, mef_action_count


def oai_save_records_from_dates(name, file_name, sickle, oai_item_iterator,
                                max_retries=0,
                                access_token=None, days_spann=30,
                                from_date=None, until_date=None,
                                verbose=False, **kwargs):
    """Harvest and save multiple records from an OAI repo.

    :param name: The name of the OAIHarvestConfig to use instead of passing
                 specific parameters.
    :param from_date: The lower bound date for the harvesting (optional).
    :param until_date: The upper bound date for the harvesting (optional).
    """
    # data on IDREF Servers starts on 2000-10-01
    name = name
    days_spann = days_spann
    last_run = None
    url, metadata_prefix, last_run, setspecs = get_info_by_oai_name(name)

    request = sickle(url, iterator=oai_item_iterator, max_retries=max_retries)

    dates_inital = {
        'from': from_date or last_run,
        'until': until_date
    }
    # Sanity check
    if dates_inital['until'] is not None \
            and dates_inital['from'] > dates_inital['until']:
        raise WrongDateCombination("'Until' date larger than 'from' date.")

    last_run_date = datetime.datetime.now()

    # If we don't have specifications for set searches the setspecs will be
    # set to e list with None to go into the retrieval loop without
    # a set definition (line 177)
    setspecs = setspecs.split() or [None]
    count = 0
    with open(file_name, 'bw') as output_file:
        for spec in setspecs:
            dates = dates_inital
            params = {
                'metadataPrefix': metadata_prefix,
                'ignore_deleted': False
            }
            if access_token:
                params['accessToken'] = access_token
            params.update(dates)
            if spec:
                params['set'] = spec

            my_from_date = parser.parse(dates['from'])
            my_until_date = last_run_date
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
                        count += 1
                        records = parse_xml_to_array(StringIO(record.raw))
                        record_id = '???'
                        field_001 = records[0]['001']
                        if field_001:
                            record_id = field_001.data
                        if verbose:
                            click.echo(
                                'OAI {name} spec({spec}): {from_d} '
                                'count:{count:>10} = {id}'.format(
                                    name=name,
                                    spec=spec,
                                    from_d=my_from_date.strftime("%Y-%m-%d"),
                                    days_spann=days_spann,
                                    count=count,
                                    id=record_id
                                )
                            )
                        rec = records[0]
                        rec.leader = rec.leader[0:9] + 'a' + rec.leader[10:]
                        output_file.write(rec.as_marc())
                except NoRecordsMatch:
                    my_from_date = my_from_date + timedelta(
                        days=days_spann + 1)
                    continue
                except Exception as err:
                    current_app.logger.error(err)

                my_from_date = my_from_date + timedelta(days=days_spann + 1)
                if verbose:
                    click.echo(
                        'OAI {name} spec({spec}): '
                        '{from_d} .. +{days_spann}'.format(
                            name=name,
                            spec=spec,
                            from_d=my_from_date.strftime("%Y-%m-%d"),
                            days_spann=days_spann
                        )
                    )
    if verbose:
        click.echo('OAI {name}: {count}'.format(
            name=name,
            count=count
        ))
    return count


def oai_get_record(id, name, transformation, record_cls, access_token=None,
                   identifier=None, dbcommit=False, reindex=False,
                   test_md5=False, verbose=False, debug=False, **kwargs):
    """Get record from an OAI repo.

    :param identifier: identifier of record.
    """
    name = name
    url, metadata_prefix, lastrun, setspecs = get_info_by_oai_name(name)

    request = Sickle(url)

    params = {}
    if access_token:
        params['accessToken'] = access_token

    params['metadataPrefix'] = metadata_prefix
    setspecs = setspecs.split()
    params['identifier'] = '{identifier}{id}'.format(identifier=identifier,
                                                     id=id)
    try:
        record = request.GetRecord(**params)
    except Exception as err:
        if debug:
            raise(err)
        return None, AgencyAction.DISCARD, MefAction.DISCARD
    records = parse_xml_to_array(StringIO(record.raw))
    rec = transformation(records[0]).json
    try:
        new_rec, action, mef_action = record_cls.create_or_update(
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
            'OAI-{name} get: {id} action: {action} {mef}'.format(
                name=name,
                id=id,
                action=action,
                mef=mef_action
            )
        )
    return new_rec, action, mef_action


def read_json_record(json_file, buf_size=1024, decoder=JSONDecoder()):
    """Read lasy json records from file.

    :param json_file: json file handle
    :param buf_size: buffer size for file read
    :param decoder: decoder to use for decoding
    :return: record Generator
    """
    buffer = json_file.read(2).replace('\n', '')
    # we have to delete the first [ for an list of records
    if buffer.startswith('['):
        buffer = buffer[1:].lstrip()
    while True:
        block = json_file.read(buf_size)
        if not block:
            break
        buffer += block.replace('\n', '')
        pos = 0
        while True:
            try:
                buffer = buffer.lstrip()
                obj, pos = decoder.raw_decode(buffer)
            except JSONDecodeError as err:
                break
            else:
                yield obj
                buffer = buffer[pos:].lstrip()

                if len(buffer) <= 0:
                    # buffer is empty read more data
                    buffer = json_file.read(buf_size)
                if buffer.startswith(','):
                    # delete records deliminators
                    buffer = buffer[1:].lstrip()


def export_json_records(pids, pid_type, output_file_name, indent=2,
                        schema=True, verbose=False):
    """Writes records from record_class to file.

    :param pids: pids to use
    :param pid_type: pid_type to use
    :param output_file_name: file name to write to
    :param indent: indent to use in output file
    :param schema: do not delete $schema
    :param verbose: verbose print
    :returns: count of records written
    """
    record_class = obj_or_import_string(
        current_app.config
        .get('RECORDS_REST_ENDPOINTS')
        .get(pid_type).get('record_class')
    )
    count = 0
    output = '['
    offset = '{character:{indent}}'.format(character=' ', indent=indent)
    with open(output_file_name, 'w') as outfile:
        for pid in pids:
            try:
                rec = record_class.get_record_by_pid(pid)
                count += 1
                if verbose:
                    msg = '{count: <8} {pid_type} export {pid}:{id}'.format(
                        count=count,
                        pid_type=pid_type,
                        pid=rec.pid,
                        id=rec.id
                    )
                    click.echo(msg)

                outfile.write(output)
                if count > 1:
                    outfile.write(',')
                if not schema:
                    rec.pop('$schema', None)
                    persons_sources = current_app.config.get(
                        'RERO_ILS_PERSONS_SOURCES', [])
                    for persons_source in persons_sources:
                        rec[persons_sources].pop('$schema', None)
                output = ''
                lines = json.dumps(rec, indent=indent).split('\n')
                for line in lines:
                    output += '\n{offset}{line}'.format(
                        offset=offset, line=line)
            except Exception as err:
                click.echo(err)
                click.echo('ERROR: Can not export pid:{pid}'.format(pid=pid))
        outfile.write(output)
        outfile.write('\n]\n')
