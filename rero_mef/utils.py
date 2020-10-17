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
import gc
import hashlib
import json
import os
import traceback
from copy import deepcopy
from datetime import datetime, timedelta
from io import StringIO
from json import JSONDecodeError, JSONDecoder
from time import sleep
from uuid import uuid4

import click
import ijson
import psycopg2
import sqlalchemy
from dateutil import parser
from flask import current_app
from invenio_db import db
from invenio_oaiharvester.api import get_info_by_oai_name
from invenio_oaiharvester.errors import InvenioOAIHarvesterConfigNotFound, \
    WrongDateCombination
from invenio_oaiharvester.models import OAIHarvestConfig
from invenio_oaiharvester.utils import get_oaiharvest_object
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_rest.utils import obj_or_import_string
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pymarc.marcxml import parse_xml_to_array
from sickle import Sickle, oaiexceptions
from sickle.iterator import OAIItemIterator
from sickle.oaiexceptions import NoRecordsMatch


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
                                   reindex=True, test_md5=True, online=False,
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

    last_run_date = datetime.now()

    # If we don't have specifications for set searches the setspecs will be
    # set to e list with None to go into the retrieval loop without
    # a set definition (line 177)
    setspecs = setspecs.split() or [None]
    count = 0
    action_count = {}
    mef_action_count = {}
    viaf_online_count = 0
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
                    count += 1
                    records = parse_xml_to_array(StringIO(record.raw))
                    try:
                        try:
                            updated = datetime.strptime(
                                records[0]['005'].data,
                                '%Y%m%d%H%M%S.%f'
                            )
                        except:
                            updated = '????'
                        rec = transformation(records[0]).json
                        pid = rec.get('pid')
                        rec, action, m_record, m_action, v_record, online = \
                            record_cls.create_or_update_agent_mef_viaf(
                                data=rec,
                                dbcommit=True,
                                reindex=True,
                                online=online,
                                verbose=verbose
                            )
                        action_count.setdefault(action.name, 0)
                        action_count[action.name] += 1
                        mef_action_count.setdefault(m_action.name, 0)
                        mef_action_count[m_action.name] += 1
                        if online:
                            viaf_online_count += 1

                        if verbose:
                            m_pid = 'Non'
                            if m_record:
                                m_pid = m_record.pid
                            v_pid = 'Non'
                            if v_record:
                                v_pid = v_record.pid
                            click.echo(
                                (
                                    'OAI {name} spec({spec}): {pid}'
                                    ' updated: {updated} {action}'
                                    ' | mef: {m_pid} {m_action}'
                                    ' | viaf: {v_pid} online: {online}'
                                ).format(
                                    name=name,
                                    spec=spec,
                                    pid=pid,
                                    action=action.value,
                                    m_pid=m_pid,
                                    m_action=m_action.value,
                                    v_pid=v_pid,
                                    online=online,
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

    last_run_date = datetime.now()

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
        return None
    records = parse_xml_to_array(StringIO(record.raw))
    trans_record = transformation(records[0]).json
    if verbose:
        click.echo(
            'OAI-{name} get: {id}'.format(
                name=name,
                id=id
            )
        )
    return trans_record


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


def number_records_in_file(json_file, type):
    """Get number of records per file."""
    count = 0
    with open(json_file, 'r',  buffering=1) as file:
        for line in file:
            if type == 'json':
                if '"pid"' in line:
                    count += 1
            elif type == 'csv':
                count += 1
    return count


def progressbar(items, length=0, verbose=False):
    """Verbose progress bar."""
    if verbose:
        with click.progressbar(
                items, label=str(length), length=length
        ) as progressbar_items:
            for item in progressbar_items:
                yield item
    else:
        for item in items:
            yield item


def get_host():
    """Get the host from the config."""
    # from flask import current_app
    # with current_app.app_context():
    #     return current_app.config.get('JSONSCHEMAS_HOST')
    return 'mef.rero.ch'


def resolve_record(path, object_class):
    """Resolve local records.

    :param path: pid for record
    :object_class: record class to use
    :returns: record for pid or {}
    """
    try:
        record = object_class.get_record_by_pid(path)
        return record
    except PIDDoesNotExistError:
        return {}


def metadata_csv_line(record, record_uuid, date):
    """Build CSV metadata table line."""
    created_date = updated_date = date
    sep = '\t'
    metadata = (
        created_date,
        updated_date,
        record_uuid,
        json.dumps(record).replace('\\', '\\\\'),
        '1',
    )
    metadata_line = sep.join(metadata)
    return metadata_line + os.linesep


def pidstore_csv_line(agent, agent_pid, record_uuid, date):
    """Build CSV pidstore table line."""
    created_date = updated_date = date
    sep = '\t'
    pidstore_data = [
        created_date,
        updated_date,
        agent,
        agent_pid,
        'R',
        'rec',
        record_uuid,
    ]
    pidstore_line = sep.join(pidstore_data)
    return pidstore_line + os.linesep


def add_agent_to_json(mef_record, agent, agent_pid):
    """Add agent ref to mef record."""
    from .mef.api import MefRecord
    ref_string = MefRecord.build_ref_string(
        agent=agent, agent_pid=agent_pid
    )
    mef_record[agent] = {'$ref': ref_string}


def raw_connection():
    """Return a raw connection to the database."""
    with current_app.app_context():
        URI = current_app.config.get('SQLALCHEMY_DATABASE_URI')
        engine = sqlalchemy.create_engine(URI)
        # conn = engine.connect()
        connection = engine.raw_connection()
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return connection


def db_copy_from(buffer, table, columns):
    """Copy data from file to db."""
    connection = raw_connection()
    cursor = connection.cursor()
    try:
        cursor.copy_from(
            file=buffer,
            table=table,
            columns=columns,
            sep='\t'
        )
        connection.commit()
    except psycopg2.DataError as error:
        current_app.logger.error('data load error: {0}'.format(error))
    # cursor.execute('VACUUM ANALYSE {table}'.format(table=table))
    # cursor.close()
    connection.close()


def db_copy_to(filehandle, table, columns):
    """Copy data from db to file."""
    connection = raw_connection()
    cursor = connection.cursor()
    try:
        cursor.copy_to(
            file=filehandle,
            table=table,
            columns=columns,
            sep='\t'
        )
        cursor.connection.commit()
    except psycopg2.DataError as error:
        current_app.logger.error(
            'data load error: {0}'.format(error)
        )
    cursor.execute('VACUUM ANALYSE {table}'.format(table=table))
    cursor.close()
    connection.close()


def bulk_index(agent, uuids, verbose=False):
    """Bulk index records."""
    if verbose:
        click.echo(' add to index: {count}'.format(count=len(uuids)))
    retry = True
    minutes = 1
    from .api import ReroMefIndexer
    while retry:
        try:
            ReroMefIndexer().bulk_index(uuids, doc_type=agent)
            retry = False
        except Exception as exc:
            msg = 'Bulk Index Error: retry in {minutes} min {exc}'.format(
                exc=exc,
                minutes=minutes
            )
            current_app.logger.error(msg)
            if verbose:
                click.secho(msg, fg='red')
            sleep(minutes * 60)
            retry = True
            minutes *= 2


def bulk_load_agent(agent, data, table, columns, bulk_count=0, verbose=False,
                    reindex=False):
    """Bulk load agent data to table."""
    if bulk_count <= 0:
        bulk_count = current_app.config.get('BULK_CHUNK_COUNT', 100000)
    count = 0
    buffer = StringIO()
    buffer_uuid = []
    index = -1
    if 'id' in columns:
        index = columns.index('id')
    start_time = datetime.now()
    with open(data, 'r', encoding='utf-8', buffering=1) as input_file:
        for line in input_file:
            count += 1
            buffer.write(line)
            if index >= 0 and reindex:
                buffer_uuid.append(line.split('\t')[index])
            if count % bulk_count == 0:
                buffer.flush()
                buffer.seek(0)
                if verbose:
                    end_time = datetime.now()
                    diff_time = end_time - start_time
                    start_time = end_time
                    click.echo(
                        '{agent} copy from file: {count} {time}s'.format(
                            agent=agent,
                            count=count,
                            time=diff_time.seconds
                        ),
                        nl=False
                    )
                db_copy_from(buffer=buffer, table=table, columns=columns)
                buffer.close()

                if index >= 0 and reindex:
                    bulk_index(agent=agent, uuids=buffer_uuid,
                               verbose=verbose)
                    buffer_uuid.clear()
                else:
                    if verbose:
                        click.echo()

                # force the Garbage Collector to release unreferenced memory
                # gc.collect()
                # new buffer
                buffer = StringIO()

        if verbose:
            end_time = datetime.now()
            diff_time = end_time - start_time
            click.echo(
                '{agent} copy from file: {count} {time}s'.format(
                    agent=agent,
                    count=count,
                    time=diff_time.seconds
                ),
                nl=False
            )
        buffer.flush()
        buffer.seek(0)
        db_copy_from(buffer=buffer, table=table, columns=columns)
        buffer.close()
        if index >= 0 and reindex:
            bulk_index(agent=agent, uuids=buffer_uuid, verbose=verbose)
            buffer_uuid.clear()
        else:
            if verbose:
                click.echo()

    # force the Garbage Collector to release unreferenced memory
    gc.collect()


def bulk_load_agent_metadata(agent, metadata, bulk_count=0, verbose=True,
                             reindex=False):
    """Bulk load agent data to metadata table."""
    agent_class = get_agent_class(agent)
    table, identifier = agent_class.get_metadata_identifier_names()
    columns = (
        'created',
        'updated',
        'id',
        'json',
        'version_id'
    )
    bulk_load_agent(
        agent=agent,
        data=metadata,
        table=table,
        columns=columns,
        bulk_count=bulk_count,
        verbose=verbose,
        reindex=reindex
    )


def bulk_load_agent_pids(agent, pidstore, bulk_count=0, verbose=True,
                         reindex=False):
    """Bulk load agent data to metadata table."""
    table = 'pidstore_pid'
    columns = (
        'created',
        'updated',
        'pid_type',
        'pid_value',
        'status',
        'object_type',
        'object_uuid',
    )
    bulk_load_agent(
        agent=agent,
        data=pidstore,
        table=table,
        columns=columns,
        bulk_count=bulk_count,
        verbose=verbose,
        reindex=reindex
    )


def bulk_load_agent_ids(agent, ids, bulk_count=0, verbose=True, reindex=False):
    """Bulk load agent data to id table."""
    agent_class = get_agent_class(agent)
    metadata, identifier = agent_class.get_metadata_identifier_names()
    columns = ('recid', )
    bulk_load_agent(
        agent=agent,
        data=ids,
        table=identifier,
        columns=columns,
        bulk_count=bulk_count,
        verbose=verbose,
        reindex=reindex
    )


def bulk_save_agent(agent, file_name, table, columns, verbose=False):
    """Bulk save agent data to file."""
    with open(file_name, 'w', encoding='utf-8') as output_file:
        db_copy_to(
            filehandle=output_file,
            table=table,
            columns=columns
        )


def bulk_save_agent_metadata(agent, file_name, verbose=False):
    """Bulk save agent data from metadata table."""
    if verbose:
        click.echo('{agent} save to file: {filename}'.format(
            agent=agent,
            filename=file_name
        ))
    agent_class = get_agent_class(agent)
    metadata, identifier = agent_class.get_metadata_identifier_names()
    columns = (
        'created',
        'updated',
        'id',
        'json',
        'version_id'
    )
    bulk_save_agent(
        agent=agent,
        file_name=file_name,
        table=metadata,
        columns=columns,
        verbose=verbose
    )


def bulk_save_agent_pids(agent, file_name, verbose=False):
    """Bulk save agent data from pids table."""
    if verbose:
        click.echo('{agent} save to file: {filename}'.format(
            agent=agent,
            filename=file_name
        ))
    table = 'pidstore_pid'
    columns = (
        'created',
        'updated',
        'pid_type',
        'pid_value',
        'status',
        'object_type',
        'object_uuid',
    )
    tmp_file_name = file_name + '_tmp'
    bulk_save_agent(
        agent=agent,
        file_name=tmp_file_name,
        table=table,
        columns=columns,
        verbose=verbose
    )
    # clean pid file
    with open(tmp_file_name, 'r') as file_in:
        with open(file_name, "w") as file_out:
            file_out.writelines(line for line in file_in if agent in line)
    os.remove(tmp_file_name)


def bulk_save_agent_ids(agent, file_name, verbose=False):
    """Bulk save agent data from id table."""
    if verbose:
        click.echo('{agent} save to file: {filename}'.format(
            agent=agent,
            filename=file_name
        ))
    agent_class = get_agent_class(agent)
    metadata, identifier = agent_class.get_metadata_identifier_names()
    columns = ('recid', )
    bulk_save_agent(
        agent=agent,
        file_name=file_name,
        table=identifier,
        columns=columns,
        verbose=verbose
    )


def create_md5(record):
    """Create md5 for record."""
    data_md5 = hashlib.md5(
        json.dumps(record, sort_keys=True).encode('utf-8')
    ).hexdigest()
    return data_md5


def add_md5(record):
    """Add md5 to json."""
    schema = None
    if record.get('$schema'):
        schema = record.pop('$schema')
    if record.get('md5'):
        record.pop('md5')
    record['md5'] = create_md5(record)
    if schema:
        record['$schema'] = schema
    return record


def add_schema(record, agent):
    """Add the $schema to the record."""
    with current_app.app_context():
        schemas = current_app.config.get('RECORDS_JSON_SCHEMA')
        if agent in schemas:
            record['$schema'] = '{base_url}{endpoint}{schema}'.format(
                base_url=current_app.config.get('RERO_MEF_APP_BASE_URL'),
                endpoint=current_app.config.get('JSONSCHEMAS_ENDPOINT'),
                schema=schemas[agent]
            )
    return record


def create_agent_csv_file(input_file, agent, pidstore, metadata):
    """Create agent csv file to load."""
    if agent == 'mef':
        agent_id_file = open('{agent}_id'.format(agent=agent),
                             'w', encoding='utf-8')
    with \
            open(input_file, 'r', encoding='utf-8') as agent_file, \
            open(metadata, 'w', encoding='utf-8') as agent_metadata_file, \
            open(pidstore, 'w', encoding='utf-8') as agent_pids_file:

        for record in ijson.items(agent_file, "item"):
            if agent == 'viaf':
                record['pid'] = record['viaf_pid']

            ordered_record = add_md5(record)
            add_schema(ordered_record, agent)

            record_uuid = str(uuid4())
            date = str(datetime.utcnow())

            agent_metadata_file.write(
                metadata_csv_line(ordered_record, record_uuid, date)
            )

            agent_pids_file.write(
                pidstore_csv_line(agent, record['pid'], record_uuid, date)
            )
            if agent == 'mef':
                agent_id_file.write(record['pid'] + os.linesep)


def get_agent_classes(without_mef_viaf=True):
    """Get agent classes from config."""
    agents = {}
    endpoints = deepcopy(current_app.config.get('RECORDS_REST_ENDPOINTS', {}))
    if without_mef_viaf:
        endpoints.pop('mef', None)
        endpoints.pop('viaf', None)
    for agent in endpoints:
        record_class = obj_or_import_string(
            endpoints[agent].get('record_class')
        )
        if record_class:
            agents[agent] = record_class
    return agents


def get_endpoint_class(agent, class_name):
    """Get agent class from config."""
    endpoints = current_app.config.get('RECORDS_REST_ENDPOINTS', {})
    endpoint = endpoints.get(agent, {})
    endpoint_class = obj_or_import_string(endpoint.get(class_name))
    return endpoint_class


def get_agent_class(agent):
    """Get agent record class from config."""
    return get_endpoint_class(agent=agent, class_name='record_class')


def get_agent_search_class(agent):
    """Get agent search class from config."""
    return get_endpoint_class(agent=agent, class_name='search_class')


def get_agent_indexer_class(agent):
    """Get agent indexer class from config."""
    return get_endpoint_class(agent=agent, class_name='indexer_class')


def write_link_json(
    agent,
    pidstore_file,
    metadata_file,
    viaf_pid,
    corresponding_data,
    agent_pid,
    verbose=False
):
    """Write a json record into file."""
    json_data = {}
    key_per_catalog_id = {
        'DNB': 'gnd_pid',
        'RERO': 'rero_pid',
        'SUDOC': 'idref_pid'
    }
    json_data['viaf_pid'] = viaf_pid
    write_to_file_viaf = False
    for key, value in corresponding_data.items():
        if key in key_per_catalog_id:
            json_data[key_per_catalog_id[key]] = value
            write_to_file_viaf = True
    write_to_file = False
    json_dump = json_data

    agent_pid = viaf_pid
    add_schema(json_dump, 'viaf')
    json_dump['pid'] = agent_pid
    del(json_dump['viaf_pid'])
    # only save viaf data with used pids
    if agent == 'viaf':
        write_to_file = write_to_file_viaf
    else:
        write_to_file = True

    if write_to_file:
        record_uuid = str(uuid4())
        date = str(datetime.utcnow())
        pidstore_file.write(
            pidstore_csv_line(agent, agent_pid, record_uuid, date)
        )
        metadata_file.write(metadata_csv_line(json_dump, record_uuid, date))
        if verbose:
            msg = '  {agent}: {data}'.format(
                agent=agent,
                data=json_dump
            )
            click.echo(msg)
    return write_to_file


def create_mef_files(
    viaf_pidstore_file,
    input_directory,
    mef_pidstore_file_name,
    mef_metadata_file_name,
    mef_ids_file_name,
    verbose=False
):
    """Create MEF csv file to load."""
    if verbose:
        click.echo('Start ***')
    pids = {}
    agent_classes = get_agent_classes()
    viaf_agent_pid_names = {}
    for agent, agent_classe in agent_classes.items():
        name = agent_classe.name
        viaf_pid_name = agent_classe.viaf_pid_name
        if viaf_pid_name:
            viaf_agent_pid_names[viaf_pid_name] = name
            file_name = os.path.join(
                input_directory,
                '{agent}_pidstore.csv'.format(agent=agent)
            )
            if os.path.exists(file_name):
                if verbose:
                    click.echo('  Read pids from: {name}'.format(
                        name=file_name)
                    )
                length = number_records_in_file(file_name, 'csv')
                pids[name] = {}
                progress = progressbar(
                    items=open(file_name, 'r'),
                    length=length,
                    verbose=verbose
                )
                for line in progress:
                    pid = line.split('\t')[3]
                    pids[name][pid] = 1

    mef_pid = 1
    corresponding_data = {}
    with open(
        mef_pidstore_file_name, 'w', encoding='utf-8'
    ) as mef_pidstore:
        with open(
            mef_metadata_file_name, 'w', encoding='utf-8'
        ) as mef_metadata:
            with open(
                mef_ids_file_name, 'w', encoding='utf-8'
            ) as mef_ids_file:
                schemas = current_app.config.get('RECORDS_JSON_SCHEMA')
                base_url = current_app.config.get('RERO_MEF_APP_BASE_URL')
                schema = '{base_url}{endpoint}{schema}'.format(
                    base_url=base_url,
                    endpoint=current_app.config.get('JSONSCHEMAS_ENDPOINT'),
                    schema=schemas['mef']
                )
                if verbose:
                    click.echo('  Create MEF with VIAF pid: {name}'.format(
                        name=viaf_pidstore_file
                    ))
                progress = progressbar(
                    items=open(str(viaf_pidstore_file), 'r', encoding='utf-8'),
                    length=number_records_in_file(viaf_pidstore_file, 'csv'),
                    verbose=verbose
                )
                for line in progress:
                    viaf_data = json.loads(line.split('\t')[3])
                    viaf_pid = viaf_data['pid']
                    corresponding_data = {
                        'pid': str(mef_pid),
                        '$schema': schema
                    }
                    for viaf_pid_name, name in viaf_agent_pid_names.items():
                        agent_pid = viaf_data.get(viaf_pid_name)
                        if agent_pid:
                            if pids.get(name, {}).get(agent_pid):
                                corresponding_data['viaf_pid'] = viaf_pid
                                pids[name].pop(agent_pid)
                                url = '{base_url}/api/{name}/{pid}'.format(
                                    base_url=base_url,
                                    name=name,
                                    pid=agent_pid
                                )
                                corresponding_data[name] = {'$ref': url}
                    if corresponding_data.get('viaf_pid'):
                        # Write MEF with VIAF to file
                        mef_uuid = str(uuid4())
                        date = str(datetime.utcnow())
                        mef_pidstore.write(
                            pidstore_csv_line(
                                'mef', str(mef_pid), mef_uuid, date)
                        )
                        mef_metadata.write(
                            metadata_csv_line(
                                corresponding_data, mef_uuid, date)
                        )
                        mef_ids_file.write(str(mef_pid) + os.linesep)
                        mef_pid += 1
                # Create MEF without VIAF
                length = 0
                for agent in pids:
                    length += len(pids[agent])
                if verbose:
                    click.echo('  Create MEF without VIAF pid: {count}'.format(
                        count=length
                    ))
                progress = progressbar(
                    items=pids,
                    length=length,
                    verbose=verbose
                )
                for agent in progress:
                    for pid in pids[agent]:
                        url = '{base_url}/api/{agent}/{pid}'.format(
                            base_url=base_url,
                            agent=agent,
                            pid=pid
                        )
                        corresponding_data = {
                            'pid': str(mef_pid),
                            '$schema': schema,
                            agent: {'$ref': url}
                        }
                        mef_uuid = str(uuid4())
                        date = str(datetime.utcnow())
                        mef_pidstore.write(
                            pidstore_csv_line('mef', str(mef_pid), mef_uuid,
                                              date)
                        )
                        mef_metadata.write(
                            metadata_csv_line(corresponding_data, mef_uuid,
                                              date)
                        )
                        mef_ids_file.write(str(mef_pid) + os.linesep)
                        mef_pid += 1
    if verbose:
        click.echo('  MEF records created: {count}'.format(count=mef_pid-1))


def create_viaf_files(
    viaf_input_file,
    viaf_pidstore_file_name,
    viaf_metadata_file_name,
    verbose=False
):
    """Create VIAF csv file to load."""
    if verbose:
        click.echo('Start ***')

    agent_pid = 0
    corresponding_data = {}
    count = 0
    with open(
        viaf_pidstore_file_name, 'w', encoding='utf-8'
    ) as viaf_pidstore:
        with open(
            viaf_metadata_file_name, 'w', encoding='utf-8'
        ) as viaf_metadata:
            with open(
                str(viaf_input_file), 'r', encoding='utf-8'
            ) as viaf_in_file:
                # get first viaf_pid
                row = viaf_in_file.readline()
                fields = row.rstrip().split('\t')
                assert len(fields) == 2
                previous_viaf_pid = fields[0].split('/')[-1]
                viaf_in_file.seek(0)
                for row in viaf_in_file:
                    fields = row.rstrip().split('\t')
                    assert len(fields) == 2
                    viaf_pid = fields[0].split('/')[-1]
                    if viaf_pid != previous_viaf_pid:
                        agent_pid += 1
                        written = write_link_json(
                            agent='viaf',
                            pidstore_file=viaf_pidstore,
                            metadata_file=viaf_metadata,
                            viaf_pid=previous_viaf_pid,
                            corresponding_data=corresponding_data,
                            agent_pid=str(agent_pid),
                            verbose=verbose
                        )
                        if written:
                            count += 1
                        corresponding_data = {}
                        previous_viaf_pid = viaf_pid
                    corresponding = fields[1].split('|')
                    if len(corresponding) == 2:
                        corresponding_data[corresponding[0]] = corresponding[1]
                # save the last record
                agent_pid += 1
                written = write_link_json(
                    agent='viaf',
                    pidstore_file=viaf_pidstore,
                    metadata_file=viaf_metadata,
                    viaf_pid=previous_viaf_pid,
                    corresponding_data=corresponding_data,
                    agent_pid=str(agent_pid),
                    verbose=verbose
                )
                if written:
                    count += 1
    if verbose:
        click.echo('  Viaf records created: {count}'.format(count=count))


def append_fixtures_new_identifiers(identifier, pids, pid_type):
    """Insert pids into the indentifier table and update its sequence."""
    with db.session.begin_nested():
        for pid in pids:
            db.session.add(identifier(recid=pid))
        max_pid = PersistentIdentifier.query.filter_by(
            pid_type=pid_type
        ).order_by(sqlalchemy.desc(
            sqlalchemy.cast(PersistentIdentifier.pid_value, sqlalchemy.Integer)
        )).first().pid_value
        identifier._set_sequence(max_pid)


def get_agents_endpoints(without_mef_viaf=True):
    """Get all agents from config."""
    agents = deepcopy(current_app.config.get('RECORDS_REST_ENDPOINTS', {}))
    if without_mef_viaf:
        agents.pop('mef', None)
        agents.pop('viaf', None)
    agents.pop('corero', None)
    return agents


def get_diff_db_es_pids(agent, verbose=False):
    """Get differences between DB and ES pids."""
    pids_db = {}
    pids_es = {}
    pids_es_double = []
    record_class = get_agent_class(agent)
    count = record_class.count()
    if verbose:
        click.echo('Get pids from DB: {count}'.format(count=count))
    progress = progressbar(
        items=record_class.get_all_pids(),
        length=count,
        verbose=verbose
    )
    for pid in progress:
        pids_db[pid] = 1
    search_class = get_agent_search_class(agent)
    count = search_class().source('pid').count()
    if verbose:
        click.echo('Get pids from ES: {count}'.format(count=count))
    progress = progressbar(
        items=search_class().source('pid').scan(),
        length=count,
        verbose=verbose
    )
    for hit in progress:
        pid = hit.pid
        if pids_es.get(pid):
            pids_es_double.append(pid)
        if pids_db.get(pid):
            pids_db.pop(pid)
        else:
            pids_es[pid] = 1
    pids_db = [v for v in pids_db]
    pids_es = [v for v in pids_es]
    if verbose:
        click.echo('Counts  DB: {dbc} ES: {esc} ES+: {esp}'.format(
            dbc=len(pids_db),
            esc=len(pids_es),
            esp=len(pids_es_double)
        ))
    return pids_db, pids_es, pids_es_double
