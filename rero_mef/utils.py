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
from functools import wraps
from io import StringIO
from json import JSONDecodeError, JSONDecoder, dumps
from time import sleep
from uuid import uuid4

import click
import ijson
import psycopg2
import requests
import sqlalchemy
from dateutil import parser
from flask import current_app
from invenio_cache.proxies import current_cache
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
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
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
            click.echo(f'OAI {name}: last run: {lastrun_date}')
        return lastrun_date
    except InvenioOAIHarvesterConfigNotFound:
        if verbose:
            click.echo((f'ERROR OAI config not found: {name}'))
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
            click.echo(f'OAI {name}: set last run: {lastrun_date}')
        return lastrun_date
    except InvenioOAIHarvesterConfigNotFound:
        if verbose:
            click.echo(f'ERROR OAI config not found: {name}')
    except parser.ParserError as err:
        if verbose:
            click.echo(f'OAI set lastrun {name}: {err}')
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

        count = 0
        while count < 5:
            try:
                self.oai_response = self.sickle.harvest(**params)
                xml = self.oai_response.xml
                count = 5
            except Exception as err:
                count += 1
                current_app.logger.error(f'Sickle harvest {count} {err}')
                sleep(60)
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
                current_app.logger.error(
                    f'ERROR HARVESTING incomplete response: '
                    f'{self.resumption_token.cursor} '
                    f'{self.resumption_token.token}'
                )
                sleep(60)
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
                                   verbose=False, debug=False,
                                   viaf_online=False, **kwargs):
    """Harvest multiple records from an OAI repo.

    :param name: The name of the OAIHarvestConfig to use instead of passing
                 specific parameters.
    :param from_date: The lower bound date for the harvesting (optional).
    :param until_date: The upper bound date for the harvesting (optional).
    """
    # data on IDREF Servers starts on 2000-10-01
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
                        except Exception as err:
                            updated = '????'
                        rec = transformation(records[0]).json
                        pid = rec.get('pid')
                        rec, action, m_record, m_action, v_record, v_online = \
                            record_cls.create_or_update_agent_mef_viaf(
                                data=rec,
                                dbcommit=True,
                                reindex=True,
                                test_md5=test_md5,
                                online=viaf_online,
                                verbose=verbose
                            )
                        action_count.setdefault(action.name, 0)
                        action_count[action.name] += 1
                        mef_action_count.setdefault(m_action.name, 0)
                        mef_action_count[m_action.name] += 1
                        if v_online:
                            viaf_online_count += 1

                        if verbose:
                            m_pid = 'Non'
                            if m_record:
                                m_pid = m_record.pid
                            v_pid = 'Non'
                            if v_record:
                                v_pid = v_record.pid
                            click.echo(
                                f'OAI {name} spec({spec}): {pid}'
                                f' updated: {updated} {action}'
                                f' | mef: {m_pid} {m_action}'
                                f' | viaf: {v_pid} online: {v_online}'
                            )
                    except Exception as err:
                        msg = f'Creating {name} {count}: {err}'
                        if rec:
                            msg += f'\n{rec}'

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
                from_date = my_from_date.strftime("%Y-%m-%d")
                click.echo(
                    f'OAI {name} {spec}: {from_date} .. +{days_spann}'
                )

    if update_last_run:
        if verbose:
            click.echo(f'OAI {name}: update last run: {last_run}')
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
                            from_date = my_from_date.strftime("%Y-%m-%d")
                            click.echo(
                                f'OAI {name} spec({spec}): {from_date} '
                                f'count:{count:>10} = {id}'
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
                    from_date = my_from_date.strftime("%Y-%m-%d")
                    click.echo(
                        f'OAI {name} spec({spec}): '
                        f'{from_date} .. +{days_spann}'
                    )
    if verbose:
        click.echo(f'OAI {name}: {count}')
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
    params['identifier'] = f'{identifier}{id}'
    try:
        record = request.GetRecord(**params)
    except Exception as err:
        if debug:
            raise Exception(err)
        return None
    records = parse_xml_to_array(StringIO(record.raw))
    trans_record = transformation(records[0]).json
    if verbose:
        click.echo(f'OAI-{name} get: {id}')
    return trans_record


def read_json_record(json_file, buf_size=1024, decoder=JSONDecoder()):
    """Read lasy JSON records from file.

    :param json_file: JSON file handle
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
    outfile = JsonWriter(output_file_name, indent=indent)
    for pid in pids:
        try:
            rec = record_class.get_record_by_pid(pid)
            count += 1
            if verbose:
                click.echo(
                    f'{count: <8} {pid_type} export {rec.pid}:{rec.id}'
                )
            if not schema:
                rec.pop('$schema', None)
                persons_sources = current_app.config.get(
                    'RERO_ILS_PERSONS_SOURCES', [])
                for persons_source in persons_sources:
                    rec[persons_source].pop('$schema', None)
            outfile.write(rec)
        except Exception as err:
            click.echo(err)
            click.echo(f'ERROR: Can not export pid:{pid}')


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
    except psycopg2.DataError as err:
        current_app.logger.error(f'data load error: {err}')
    # cursor.execute(f'VACUUM ANALYSE {table}')
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
    except psycopg2.DataError as err:
        current_app.logger.error(f'data load error: {err}')
    cursor.execute(f'VACUUM ANALYSE {table}')
    cursor.close()
    connection.close()


def bulk_index(agent, uuids, verbose=False):
    """Bulk index records."""
    if verbose:
        click.echo(f' add to index: {len(uuids)}')
    retry = True
    minutes = 1
    from .api import ReroIndexer
    while retry:
        try:
            ReroIndexer().bulk_index(uuids, doc_type=agent)
            retry = False
        except Exception as exc:
            msg = f'Bulk Index Error: retry in {minutes} min {exc}'
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
                        f'{agent} copy from file: '
                        f'{count} {diff_time.seconds}s',
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
                '{agent} copy from file: {count} {diff_time.seconds}s',
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


def bulk_load_metadata(agent, metadata, bulk_count=0, verbose=True,
                       reindex=False):
    """Bulk load agent data to metadata table."""
    agent_class = get_entity_class(agent)
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


def bulk_load_pids(agent, pidstore, bulk_count=0, verbose=True, reindex=False):
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


def bulk_load_ids(agent, ids, bulk_count=0, verbose=True, reindex=False):
    """Bulk load agent data to id table."""
    agent_class = get_entity_class(agent)
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


def bulk_save_metadata(agent, file_name, verbose=False):
    """Bulk save agent data from metadata table."""
    if verbose:
        click.echo(f'{agent} save to file: {file_name}')
    agent_class = get_entity_class(agent)
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


def bulk_save_pids(agent, file_name, verbose=False):
    """Bulk save agent data from pids table."""
    if verbose:
        click.echo(f'{agent} save to file: {file_name}')
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


def bulk_save_ids(agent, file_name, verbose=False):
    """Bulk save agent data from id table."""
    if verbose:
        click.echo(f'{agent} save to file: {file_name}')
    agent_class = get_entity_class(agent)
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
            base_url = current_app.config.get('RERO_MEF_APP_BASE_URL')
            endpoint = current_app.config.get('JSONSCHEMAS_ENDPOINT')
            schema = schemas[agent]
            record['$schema'] = f'{base_url}{endpoint}{schema}'
    return record


def create_csv_file(input_file, agent, pidstore, metadata):
    """Create agent CSV file to load."""
    count = 0
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
            count += 1
    return count


def get_entity_classes(without_mef_viaf=True):
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


def get_endpoint_class(entity, class_name):
    """Get entity class from config."""
    endpoints = current_app.config.get('RECORDS_REST_ENDPOINTS', {})
    endpoint = endpoints.get(entity, {})
    endpoint_class = obj_or_import_string(endpoint.get(class_name))
    return endpoint_class


def get_entity_class(entity):
    """Get entity record class from config."""
    return get_endpoint_class(entity=entity, class_name='record_class')


def get_entity_search_class(entity):
    """Get entity search class from config."""
    return get_endpoint_class(entity=entity, class_name='search_class')


def get_entity_indexer_class(entity):
    """Get entity indexer class from config."""
    return get_endpoint_class(entity=entity, class_name='indexer_class')


def write_link_json(
    agent,
    pidstore_file,
    metadata_file,
    viaf_pid,
    corresponding_data,
    agent_pid,
    verbose=False
):
    """Write a JSON record into file."""
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
    # only save VIAF data with used pids
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
            click.echo(f'  {agent}: {json_dump}')
    return write_to_file


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


def get_diff_db_es_pids(agent, verbose=False):
    """Get differences between DB and ES pids."""
    pids_db = {}
    pids_es = {}
    pids_es_double = []
    record_class = get_entity_class(agent)
    count = record_class.count()
    if verbose:
        click.echo(f'Get pids from DB: {count}')
    progress = progressbar(
        items=record_class.get_all_pids(),
        length=count,
        verbose=verbose
    )
    for pid in progress:
        pids_db[pid] = 1
    search_class = get_entity_search_class(agent)
    count = search_class().source('pid').count()
    if verbose:
        click.echo(f'Get pids from ES: {count}')
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
        click.echo(f'Counts  DB: {len(pids_db)} ES: {len(pids_es)} '
                   f'ES+: {len(pids_es_double)}')
    return pids_db, pids_es, pids_es_double


def set_timestamp(name, **kwargs):
    """Set timestamp in current cache.

    Allows to timestamp functionality and monitoring of the changed
    timestamps externaly via url requests.

    :param name: name of time stamp.
    :returns: time of time stamp
    """
    time_stamps = current_cache.get('timestamps')
    if not time_stamps:
        time_stamps = {}
    utc_now = datetime.utcnow()
    time_stamps[name] = {}
    time_stamps[name]['time'] = utc_now
    for key, value in kwargs.items():
        time_stamps[name][key] = value
    current_cache.set('timestamps', time_stamps)
    return utc_now


def get_timestamp(name):
    """Get timestamp in current cache.

    :param name: name of time stamp.
    :returns: time of time stamp
    """
    time_stamps = current_cache.get('timestamps')
    if not time_stamps:
        return None
    return time_stamps.get(name)


def settimestamp(func):
    """Set timestamp function wrapper."""
    @wraps(func)
    def wrapped(*args, **kwargs):
        result = func(*args, **kwargs)
        set_timestamp(func.__name__, result=result)
        return result
    return wrapped


class JsonWriter(object):
    """Json Writer."""

    count = 0

    def __init__(self, filename, indent=2):
        """Constructor.

        :params filename: File name of the file to be written.
        :param indent: indentation.
        """
        self.indent = indent
        self.file_handle = open(filename, 'w')
        self.file_handle.write('[')

    def __del__(self):
        """Destructor."""
        if self.file_handle:
            self.file_handle.write('\n]')
            self.file_handle.close()
            self.file_handle = None

    def write(self, data):
        """Write data to file.

        :param data: JSON data to write into the file.
        """
        if self.count > 0:
            self.file_handle.write(',')
        if self.indent:
            for line in dumps(data, indent=self.indent).split('\n'):
                self.file_handle.write(f'\n{" ".ljust(self.indent)}')
                self.file_handle.write(line)
        else:
            self.file_handle.write(dumps(data), separators=(',', ':'))
        self.count += 1

    def close(self):
        """Close file."""
        self.__del__()


def requests_retry_session(retries=3, backoff_factor=0.3,
                           status_forcelist=(500, 502, 504), session=None):
    """Request retry session.

    :params retries: The total number of retry attempts to make.
    :params backoff_factor: Sleep between failed requests.
        {backoff factor} * (2 ** ({number of total retries} - 1))
    :params status_forcelist: The HTTP response codes to retry on..
    :params session: Session to use.

    """
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
