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
import gc
import hashlib
import json
import os
from copy import deepcopy
from datetime import datetime, timedelta, timezone
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

# Hours can not be retrieved by get_info_by_oai_name
# TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
TIME_FORMAT = '%Y-%m-%d'


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
            lastrun_date = parser.isoparse(date)
        oai_source.update_lastrun(lastrun_date)
        oai_source.save()
        db.session.commit()
        if verbose:
            click.echo(f'OAI {name}: set last run: {lastrun_date}')
        return lastrun_date
    except InvenioOAIHarvesterConfigNotFound:
        if verbose:
            click.echo(f'ERROR OAI config not found: {name}')
    except ValueError as err:
        if verbose:
            click.echo(f'OAI set lastrun {name}: {err}')
    return None


class MyOAIItemIterator(OAIItemIterator):
    """OAI item iterator with accessToken."""

    def next_resumption_token_and_items(self):
        """Get next resumtion token and items."""
        self.resumption_token = self._get_resumption_token()
        self._items = self.oai_response.xml.iterfind(
            f'.//{self.sickle.oai_namespace}{self.element}')

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
            f'.//{self.sickle.oai_namespace}error')
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
                f'.//{self.sickle.oai_namespace}resumptionToken')

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
                                   transformation, record_class, max_retries=0,
                                   access_token=None, days_span=30,
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
    from rero_mef.api import Action

    # data on IDREF Servers starts on 2000-10-01
    url, metadata_prefix, last_run, setspecs = get_info_by_oai_name(name)

    request = sickle(url, iterator=oai_item_iterator, max_retries=max_retries)

    dates_inital = {
        'from': from_date or last_run,
        'until': until_date or datetime.now().isoformat()
    }
    update_last_run = from_date is None and until_date is None
    # Sanity check
    if dates_inital['until'] is not None \
            and dates_inital['from'] > dates_inital['until']:
        raise WrongDateCombination("'Until' date larger than 'from' date.")

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
        if spec:
            params['set'] = spec

        from_date = parser.isoparse(dates_inital['from'])
        real_until_date = parser.isoparse(dates_inital['until'])
        while from_date <= real_until_date:
            until_date = from_date + timedelta(days=days_span)
            until_date = min(until_date, real_until_date)
            dates = {
                'from': from_date.strftime(TIME_FORMAT),
                'until': until_date.strftime(TIME_FORMAT)
            }
            params |= dates

            try:
                for idx, record in enumerate(request.ListRecords(**params), 1):
                    records = parse_xml_to_array(StringIO(record.raw))
                    try:
                        try:
                            updated = datetime.strptime(
                                records[0]['005'].data,
                                '%Y%m%d%H%M%S.%f'
                            )
                        except Exception as err:
                            updated = '????'
                        if rec := transformation(
                                records[0], logger=current_app.logger).json:
                            if msg := rec.get('NO TRANSFORMATION'):
                                if verbose:
                                    pid = rec.get('pid', '???')
                                    click.secho(
                                        f'NO TRANSFORMATION '
                                        f'{name} {idx} {pid}: {msg}',
                                        fg='yellow'
                                    )
                            else:
                                pid = rec.get('pid')
                                record, action = record_class.create_or_update(
                                    data=rec,
                                    dbcommit=True,
                                    reindex=True,
                                    test_md5=test_md5
                                )
                                count += 1
                                action_count.setdefault(action.name, 0)
                                action_count[action.name] += 1
                                if action in [
                                    Action.CREATE,
                                    Action.UPDATE,
                                    Action.REPLACE
                                ]:
                                    m_record, m_action = \
                                        record.create_or_update_mef(
                                            dbcommit=True, reindex=True)
                                else:
                                    m_action = Action.UPTODATE
                                    m_record = None
                                mef_action_count.setdefault(m_action.name, 0)
                                mef_action_count[m_action.name] += 1

                                if verbose:
                                    msg = (
                                        f'OAI {name} spec({spec}): {pid}'
                                        f' updated: {updated} {action.name}'
                                    )
                                    if m_record:
                                        msg = (
                                            f'{msg} | mef: {m_record.pid} '
                                            f'{m_action.name}'
                                        )
                                        if viaf_pid := m_record.get(
                                                'viaf_pid'):
                                            msg = f'{msg} | viaf: {viaf_pid}'
                                    click.echo(msg)
                        elif verbose:
                            click.echo(
                                f'NO TRANSFORMATION: {name} {idx}'
                                f'\n{records[0]}'
                            )
                    except Exception as err:
                        msg = f'Creating {name} {idx}: {err}'
                        if rec:
                            msg += f'\n{rec}'
                        current_app.logger.error(
                            msg,
                            exc_info=debug,
                            stack_info=debug
                        )
            except NoRecordsMatch:
                from_date = from_date + timedelta(days=days_span + 1)
                continue
            except Exception as err:
                current_app.logger.error(
                    err,
                    exc_info=debug,
                    stack_info=debug
                )
                count = -1
                if verbose:
                    click.echo(
                        f'OAI {name} {spec}: '
                        f'{from_date.strftime(TIME_FORMAT)} .. '
                        f'{until_date.strftime(TIME_FORMAT)}'
                    )
            from_date = from_date + timedelta(days=days_span + 1)

    if update_last_run:
        last_run = dates_inital['until']
        if verbose:
            click.echo(f'OAI {name}: update last run: {last_run}')
        oai_source = get_oaiharvest_object(name)
        oai_source.update_lastrun(parser.isoparse(last_run))
        oai_source.save()
        db.session.commit()
    return count, action_count, mef_action_count


def oai_save_records_from_dates(name, file_name, sickle, oai_item_iterator,
                                max_retries=0,
                                access_token=None, days_span=30,
                                from_date=None, until_date=None,
                                verbose=False, **kwargs):
    """Harvest and save multiple records from an OAI repo.

    :param name: The name of the OAIHarvestConfig to use instead of passing
                 specific parameters.
    :param from_date: The lower bound date for the harvesting (optional).
    :param until_date: The upper bound date for the harvesting (optional).
    """
    url, metadata_prefix, last_run, setspecs = get_info_by_oai_name(name)

    request = sickle(url, iterator=oai_item_iterator, max_retries=max_retries)

    dates_inital = {
        'from': from_date or last_run,
        'until': until_date or datetime.now().isoformat()
    }
    # Sanity check
    if dates_inital['from'] > dates_inital['until']:
        raise WrongDateCombination("'Until' date larger than 'from' date.")

    # If we don't have specifications for set searches the setspecs will be
    # set to e list with None to go into the retrieval loop without
    # a set definition (line 177)
    setspecs = setspecs.split() or [None]
    count = 0
    with open(file_name, 'bw') as output_file:
        for spec in setspecs:
            params = {
                'metadataPrefix': metadata_prefix,
                'ignore_deleted': False
            }
            if access_token:
                params['accessToken'] = access_token
            if spec:
                params['set'] = spec

            from_date = parser.isoparse(dates_inital['from'])
            real_until_date = parser.isoparse(dates_inital['until'])
            while from_date <= real_until_date:
                until_date = from_date + timedelta(days=days_span)
                if until_date > real_until_date:
                    until_date = real_until_date
                dates = {
                    'from': from_date.strftime(TIME_FORMAT),
                    'until': until_date.strftime(TIME_FORMAT)
                }
                params |= dates
                try:
                    for record in request.ListRecords(**params):
                        count += 1
                        records = parse_xml_to_array(StringIO(record.raw))
                        rec = records[0]
                        if verbose:
                            click.echo(
                                f'OAI {name} spec({spec}): '
                                f'{from_date.strftime(TIME_FORMAT)} '
                                f'count:{count:>10} = {rec["001"].data}'
                            )
                        rec.leader = f'{rec.leader[:9]}a{rec.leader[10:]}'
                        output_file.write(rec.as_marc())
                except NoRecordsMatch:
                    from_date = from_date + timedelta(days=days_span + 1)
                    continue
                except Exception as err:
                    current_app.logger.error(err)
                if verbose:
                    click.echo(
                        f'OAI {name} {spec}: '
                        f'{from_date.strftime(TIME_FORMAT)} .. '
                        f'{until_date.strftime(TIME_FORMAT)}'
                    )
                from_date = from_date + timedelta(days=days_span + 1)
    if verbose:
        click.echo(f'OAI {name}: {count}')
    return count


def oai_get_record(id, name, transformation, access_token=None,
                   identifier=None, debug=False, **kwargs):
    """Get record from an OAI repo.

    :param identifier: identifier of record.
    """
    url, metadata_prefix, lastrun, setspecs = get_info_by_oai_name(name)

    request = Sickle(
        endpoint=url,
        max_retries=5,
        default_retry_after=10,
        retry_status_codes=[423, 503]
    )

    params = {
        'metadataPrefix': metadata_prefix,
        'identifier': f'{identifier}{id}'
    }
    full_url = f'{url}?verb=GetRecord&metadataPrefix={metadata_prefix}'
    full_url = f'{full_url}&identifier={identifier}{id}'

    if access_token:
        params['accessToken'] = access_token
        full_url = f'{full_url}&accessToken={access_token}'

    try:
        record = request.GetRecord(**params)
        msg = f'OAI-{name:<12} get: {id:<15} {full_url} | OK'
    except Exception as err:
        msg = f'OAI-{name:<12} get: {id:<15} {full_url} | NO RECORD'
        if debug:
            raise
        return None, msg
    records = parse_xml_to_array(StringIO(record.raw))
    if debug:
        from rero_mef.marctojson.helper import display_record
        display_record(records[0])
    trans_record = transformation(records[0], logger=current_app.logger).json
    return trans_record, msg


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
            except JSONDecodeError:
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
    record_class = get_entity_class(pid_type)
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
                for source in ('idref', 'gnd', 'rero'):
                    if source in rec:
                        rec[source].pop('$schema', None)
            outfile.write(rec)
        except Exception as err:
            click.echo(err)
            click.echo(f'ERROR: Can not export pid:{pid}')


def number_records_in_file(json_file, file_type):
    """Get number of records per file."""
    count = 0
    with open(json_file, 'r',  buffering=1) as file:
        for line in file:
            if file_type == 'json' and '"pid"' in line or file_type == 'csv':
                count += 1
    return count


def progressbar(items, length=0, verbose=False):
    """Verbose progress bar."""
    if verbose:
        with click.progressbar(
                    items, label=str(length), length=length
                ) as progressbar_items:
            yield from progressbar_items
    else:
        yield from items


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
        return object_class.get_record_by_pid(path)
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


def pidstore_csv_line(entity, entity_pid, record_uuid, date):
    """Build CSV pidstore table line."""
    created_date = updated_date = date
    sep = '\t'
    pidstore_data = [
        created_date,
        updated_date,
        entity,
        entity_pid,
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


def bulk_index(entity, uuids, verbose=False):
    """Bulk index records."""
    if verbose:
        click.echo(f' add to index: {len(uuids)}')
    retry = True
    minutes = 1
    from .api import ReroIndexer
    while retry:
        try:
            ReroIndexer().bulk_index(uuids, doc_type=entity)
            retry = False
        except Exception as exc:
            msg = f'Bulk Index Error: retry in {minutes} min {exc}'
            current_app.logger.error(msg)
            if verbose:
                click.secho(msg, fg='red')
            sleep(minutes * 60)
            retry = True
            minutes *= 2


def bulk_load_entity(entity, data, table, columns, bulk_count=0, verbose=False,
                     reindex=False):
    """Bulk load entity data to table."""
    if bulk_count <= 0:
        bulk_count = current_app.config.get('BULK_CHUNK_COUNT', 100000)
    count = 0
    buffer = StringIO()
    buffer_uuid = []
    index = columns.index('id') if 'id' in columns else -1
    start_time = datetime.now(timezone.utc)
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
                    end_time = datetime.now(timezone.utc)
                    diff_time = end_time - start_time
                    start_time = end_time
                    click.echo(
                        f'{entity} copy from file: '
                        f'{count} {diff_time.seconds}s',
                        nl=False
                    )
                db_copy_from(buffer=buffer, table=table, columns=columns)
                buffer.close()

                if index >= 0 and reindex:
                    bulk_index(entity=entity, uuids=buffer_uuid,
                               verbose=verbose)
                    buffer_uuid.clear()
                elif verbose:
                    click.echo()

                # force the Garbage Collector to release unreferenced memory
                # gc.collect()
                # new buffer
                buffer = StringIO()

        if verbose:
            end_time = datetime.now(timezone.utc)
            diff_time = end_time - start_time
            click.echo(
                f'{entity} copy from file: {count} {diff_time.seconds}s',
                nl=False
            )
        buffer.flush()
        buffer.seek(0)
        db_copy_from(buffer=buffer, table=table, columns=columns)
        buffer.close()
        if index >= 0 and reindex:
            bulk_index(entity=entity, uuids=buffer_uuid, verbose=verbose)
            buffer_uuid.clear()
        elif verbose:
            click.echo()

    # force the Garbage Collector to release unreferenced memory
    gc.collect()


def bulk_load_metadata(entity, metadata, bulk_count=0, verbose=True,
                       reindex=False):
    """Bulk load entity data to metadata table."""
    entity_class = get_entity_class(entity)
    table, identifier = entity_class.get_metadata_identifier_names()
    columns = (
        'created',
        'updated',
        'id',
        'json',
        'version_id'
    )
    bulk_load_entity(
        entity=entity,
        data=metadata,
        table=table,
        columns=columns,
        bulk_count=bulk_count,
        verbose=verbose,
        reindex=reindex
    )


def bulk_load_pids(entity, pidstore, bulk_count=0, verbose=True,
                   reindex=False):
    """Bulk load entity data to metadata table."""
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
    bulk_load_entity(
        entity=entity,
        data=pidstore,
        table=table,
        columns=columns,
        bulk_count=bulk_count,
        verbose=verbose,
        reindex=reindex
    )


def bulk_load_ids(entity, ids, bulk_count=0, verbose=True, reindex=False):
    """Bulk load entity data to id table."""
    entity_class = get_entity_class(entity)
    metadata, identifier = entity_class.get_metadata_identifier_names()
    columns = ('recid', )
    bulk_load_entity(
        entity=entity,
        data=ids,
        table=identifier,
        columns=columns,
        bulk_count=bulk_count,
        verbose=verbose,
        reindex=reindex
    )


def bulk_save_entity(file_name, table, columns, verbose=False):
    """Bulk save entity data to file."""
    with open(file_name, 'w', encoding='utf-8') as output_file:
        db_copy_to(
            filehandle=output_file,
            table=table,
            columns=columns
        )


def bulk_save_metadata(entity, file_name, verbose=False):
    """Bulk save entity data from metadata table."""
    if verbose:
        click.echo(f'{entity} save to file: {file_name}')
    entity_class = get_entity_class(entity)
    metadata, identifier = entity_class.get_metadata_identifier_names()
    columns = (
        'created',
        'updated',
        'id',
        'json',
        'version_id'
    )
    bulk_save_entity(
        file_name=file_name,
        table=metadata,
        columns=columns,
        verbose=verbose
    )


def bulk_save_pids(entity, file_name, verbose=False):
    """Bulk save entity data from pids table."""
    if verbose:
        click.echo(f'{entity} save to file: {file_name}')
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
    tmp_file_name = f'{file_name}_tmp'
    bulk_save_entity(
        file_name=tmp_file_name,
        table=table,
        columns=columns,
        verbose=verbose
    )
    # clean pid file
    with open(tmp_file_name, 'r') as file_in:
        with open(file_name, "w") as file_out:
            file_out.writelines(line for line in file_in if entity in line)
    os.remove(tmp_file_name)


def bulk_save_ids(entity, file_name, verbose=False):
    """Bulk save entity data from id table."""
    if verbose:
        click.echo(f'{entity} save to file: {file_name}')
    entity_class = get_entity_class(entity)
    metadata, identifier = entity_class.get_metadata_identifier_names()
    columns = ('recid', )
    bulk_save_entity(
        file_name=file_name,
        table=identifier,
        columns=columns,
        verbose=verbose
    )


def create_md5(record):
    """Create md5 for record."""
    return hashlib.md5(
        json.dumps(record, sort_keys=True).encode('utf-8')
    ).hexdigest()


def add_md5(record):
    """Add md5 to json."""
    schema = record.pop('$schema') if record.get('$schema') else None
    if record.get('md5'):
        record.pop('md5')
    record['md5'] = create_md5(record)
    if schema:
        record['$schema'] = schema
    return record


def add_schema(record, entity):
    """Add the $schema to the record."""
    with current_app.app_context():
        schemas = current_app.config.get('RECORDS_JSON_SCHEMA')
        if entity in schemas:
            base_url = current_app.config.get('RERO_MEF_APP_BASE_URL')
            endpoint = current_app.config.get('JSONSCHEMAS_ENDPOINT')
            schema = schemas[entity]
            record['$schema'] = f'{base_url}{endpoint}{schema}'
    return record


def create_csv_file(input_file, entity, pidstore, metadata):
    """Create entity CSV file to load."""
    count = 0
    with \
            open(input_file, 'r', encoding='utf-8') as entity_file, \
            open(metadata, 'w', encoding='utf-8') as entity_metadata_file, \
            open(pidstore, 'w', encoding='utf-8') as entity_pids_file:

        for record in ijson.items(entity_file, "item"):
            if entity == 'viaf':
                record['pid'] = record['viaf_pid']

            ordered_record = add_md5(record)
            add_schema(ordered_record, entity)

            record_uuid = str(uuid4())
            date = str(datetime.now(timezone.utc))

            entity_metadata_file.write(
                metadata_csv_line(ordered_record, record_uuid, date)
            )

            entity_pids_file.write(
                pidstore_csv_line(entity, record['pid'], record_uuid, date)
            )
            count += 1
    return count


def get_entity_classes(without_mef_viaf=True):
    """Get entity classes from config."""
    entities = {}
    endpoints = deepcopy(current_app.config.get('RECORDS_REST_ENDPOINTS', {}))
    if without_mef_viaf:
        endpoints.pop('mef', None)
        endpoints.pop('viaf', None)
        endpoints.pop('comef', None)
    for entity in endpoints:
        if record_class := obj_or_import_string(
                endpoints[entity].get('record_class')):
            entities[entity] = record_class
    return entities


def get_endpoint_class(entity, class_name):
    """Get entity class from config."""
    endpoints = current_app.config.get('RECORDS_REST_ENDPOINTS', {})
    if endpoint := endpoints.get(entity, {}):
        return obj_or_import_string(endpoint.get(class_name))


def get_entity_class(entity):
    """Get entity record class from config."""
    if entity := get_endpoint_class(entity=entity, class_name='record_class'):
        return entity


def get_entity_search_class(entity):
    """Get entity search class from config."""
    if search := get_endpoint_class(entity=entity, class_name='search_class'):
        return search


def get_entity_indexer_class(entity):
    """Get entity indexer class from config."""
    if search := get_endpoint_class(entity=entity, class_name='indexer_class'):
        return search


def write_viaf_json(
    pidstore_file,
    metadata_file,
    viaf_pid,
    corresponding_data,
    verbose=False
):
    """Write a JSON record into VIAF file."""
    from rero_mef.agents import AgentViafRecord
    json_data = {}
    for source, value in corresponding_data.items():
        if source in AgentViafRecord.sources:
            key = AgentViafRecord.sources[source]
            if pid := value.get('pid'):
                json_data[f'{key}_pid'] = pid
                if url := value.get('url'):
                    json_data[key] = url
        elif source == 'Wikipedia':
            if pid := value.get('pid'):
                json_data['wiki_pid'] = pid
            if url := value.get('url'):
                json_data['wiki'] = url
        elif source == 'Identities':
            json_data['worldcat'] = value.get('url')

    add_schema(json_data, 'viaf')
    json_data['pid'] = viaf_pid
    # only save VIAF data with used pids
    record_uuid = str(uuid4())
    date = str(datetime.now(timezone.utc))
    pidstore_file.write(
        pidstore_csv_line('viaf', viaf_pid, record_uuid, date)
    )
    metadata_file.write(metadata_csv_line(json_data, record_uuid, date))
    if verbose:
        click.echo(f'  VIAF: {json_data}')


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
    utc_now = datetime.now(timezone.utc)
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
    return time_stamps.get(name) if time_stamps else None


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

    def __enter__(self):
        """Context manager enter."""
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        """Context manager exit.

        :params exception_type: indicates class of exception.
        :params exception_value: indicates type of exception.
            like divide_by_zero error, floating_point_error,
            which are types of arithmetic exception.
        :params exception_traceback: traceback is a report which has all
            of the information needed to solve the exception.
        """
        self.__del__()

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


def mef_get_all_missing_entity_pids(mef_class, entity, verbose=False):
    """Get all missing entity pids.

    :param mef_class: MEF class to use.
    :param entity: entity name to get the missing pids.
    :param verbose: Verbose.
    :returns: Missing VIAF pids.
    """
    record_class = get_entity_class(entity)
    non_existing_pids = {}
    no_pids = []
    if verbose:
        click.echo(f'Get pids from {entity} ...')
    progress = progressbar(
        items=record_class.get_all_pids(),
        length=record_class.count(),
        verbose=verbose
    )
    missing_pids = {pid: 1 for pid in progress}
    name = record_class.name
    if verbose:
        click.echo(f'Get pids for {name} from MEF and calculate missing ...')
    query = mef_class.search().filter('exists', field=name)
    progress = progressbar(
        items=query.source(['pid', name]).scan(),
        length=query.count(),
        verbose=True
    )
    for hit in progress:
        data = hit.to_dict()
        if entity_pid := data.get(name, {}).get('pid'):
            res = missing_pids.pop(entity_pid, False)
            if not res:
                non_existing_pids[hit.pid] = entity_pid
        else:
            no_pids.append(hit.pid)
    return list(missing_pids), non_existing_pids, no_pids


def get_mefs_endpoints():
    """Get all enpoints for MEF's."""
    from rero_mef.agents import AgentMefRecord
    from rero_mef.agents.utils import get_agent_endpoints
    from rero_mef.concepts import ConceptMefRecord
    from rero_mef.concepts.utils import get_concept_endpoints

    mefs = [{
        'mef_class': AgentMefRecord,
        'endpoints': get_agent_endpoints()
    }]
    mefs.append({
        'mef_class': ConceptMefRecord,
        'endpoints': get_concept_endpoints()
    })
    return mefs


def generate(search, deleted):
    """Lagging genarator."""
    yield '['
    idx = 0
    for hit in search.scan():
        if idx != 0:
            yield ', '
        yield json.dumps(hit.to_dict())
        idx += 1
    for idx_deleted, record in enumerate(deleted):
        if idx + idx_deleted != 0:
            yield ', '
        yield json.dumps(record)
    yield ']'


def requests_retry_session(retries=5, backoff_factor=0.5,
                           status_forcelist=(500, 502, 504), session=None):
    """Request retry session.

    :params retries: The total number of retry attempts to make.
    :params backoff_factor: Sleep between failed requests.
        {backoff factor} * (2 ** ({number of total retries} - 1))
    :params status_forcelist: The HTTP response codes to retry on..
    :params session: Session to use.
    :returns: http request session.

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
