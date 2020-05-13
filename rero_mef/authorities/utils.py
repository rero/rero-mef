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

"""Utils for authorities."""

import gc
import hashlib
import json
import os
from datetime import datetime
from io import StringIO
from time import sleep
from uuid import uuid4

import click
import ijson
import psutil
import psycopg2
import sqlalchemy
from flask import current_app
from invenio_db import db
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.api import Record
from invenio_records_rest.utils import obj_or_import_string
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def get_host():
    """Get the host from the config."""
    # from flask import current_app
    # with current_app.app_context():
    #     return current_app.config.get('JSONSCHEMAS_HOST')
    return 'mef.rero.ch'


def resolve_record(path, object_class):
    """Resolve local records."""
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


def pidstore_csv_line(agency, agency_pid, record_uuid, date):
    """Build CSV pidstore table line."""
    created_date = updated_date = date
    sep = '\t'
    pidstore_data = [
        created_date,
        updated_date,
        agency,
        agency_pid,
        'R',
        'rec',
        record_uuid,
    ]
    pidstore_line = sep.join(pidstore_data)
    return pidstore_line + os.linesep


def add_agency_to_json(mef_record, agency, agency_pid):
    """Add agency ref to mef record."""
    from .mef.api import MefRecord
    ref_string = MefRecord.build_ref_string(
        agency=agency, agency_pid=agency_pid
    )
    mef_record[agency] = {'$ref': ref_string}


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
        cursor.connection.commit()
    except psycopg2.DataError as error:
        current_app.logger.error('data load error: {0}'.format(error))
    cursor.execute('VACUUM ANALYSE {table}'.format(table=table))
    cursor.close()
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


def bulk_index(agency, uuids, verbose=False):
    """Bulk index records."""
    if verbose:
        click.echo(' add to index: {count}'.format(count=len(uuids)))
    retry = True
    minutes = 1
    from .api import AuthRecordIndexer
    while retry:
        try:
            AuthRecordIndexer().bulk_index(uuids, doc_type=agency)
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


def print_memory(verbose, message):
    """Print memory usage."""
    if verbose:
        process = psutil.Process(os.getpid())
        click.echo(
            '{message} memory: {memory:.2f} MB {count}'.format(
                message=message,
                memory=process.memory_info().rss / 1024 / 1024,
                count=gc.get_count()
            )
        )


def bulk_load_agency(agency, data, table, columns,
                     bulk_count=0, verbose=False,
                     reindex=False):
    """Bulk load agency data to table."""
    if bulk_count <= 0:
        bulk_count = current_app.config.get('BULK_CHUNK_COUNT', 100000)
    count = 0
    buffer = StringIO()
    buffer_uuid = []
    index = -1
    if 'id' in columns:
        index = columns.index('id')
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
                    click.echo(
                        '{agency} copy from file: {count}'.format(
                            agency=agency,
                            count=count
                        ),
                        nl=False
                    )
                db_copy_from(buffer=buffer, table=table, columns=columns)
                buffer.close()

                if index >= 0 and reindex:
                    bulk_index(agency=agency, uuids=buffer_uuid,
                               verbose=verbose)
                    buffer_uuid.clear()
                else:
                    if verbose:
                        click.echo()

                # force the Garbage Collector to release unreferenced memory
                gc.collect()
                # new buffer
                buffer = StringIO()

        if verbose:
            click.echo(
                '{agency} copy from file: {count}'.format(
                    agency=agency,
                    count=count
                ),
                nl=False
            )
        buffer.flush()
        buffer.seek(0)
        db_copy_from(buffer=buffer, table=table, columns=columns)
        buffer.close()
        if index >= 0 and reindex:
            bulk_index(agency=agency, uuids=buffer_uuid, verbose=verbose)
            buffer_uuid.clear()
        else:
            if verbose:
                click.echo()

    # force the Garbage Collector to release unreferenced memory
    gc.collect()


def bulk_load_agency_metadata(agency, metadata, bulk_count=0,
                              verbose=True, reindex=False):
    """Bulk load agency data to metadata table."""
    table = '{agency}_metadata'.format(agency=agency)
    columns = (
        'created',
        'updated',
        'id',
        'json',
        'version_id'
    )
    bulk_load_agency(
        agency=agency,
        data=metadata,
        table=table,
        columns=columns,
        bulk_count=bulk_count,
        verbose=verbose,
        reindex=reindex
    )


def bulk_load_agency_pids(agency, pidstore, bulk_count=0,
                          verbose=True, reindex=False):
    """Bulk load agency data to metadata table."""
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
    bulk_load_agency(
        agency=agency,
        data=pidstore,
        table=table,
        columns=columns,
        bulk_count=bulk_count,
        verbose=verbose,
        reindex=reindex
    )


def bulk_load_agency_ids(agency, ids, bulk_count=0,
                         verbose=True, reindex=False):
    """Bulk load agency data to id table."""
    table = '{agency}_id'.format(agency=agency)
    columns = ('recid', )
    bulk_load_agency(
        agency=agency,
        data=ids,
        table=table,
        columns=columns,
        bulk_count=bulk_count,
        verbose=verbose,
        reindex=reindex
    )


def bulk_save_agency(agency, file_name, table, columns, verbose=False):
    """Bulk save agency data to file."""
    with open(file_name, 'w', encoding='utf-8') as output_file:
        db_copy_to(
            filehandle=output_file,
            table=table,
            columns=columns
        )


def bulk_save_agency_metadata(agency, file_name, verbose=False):
    """Bulk save agency data from metadata table."""
    if verbose:
        click.echo('{agency} save to file: {filename}'.format(
            agency=agency,
            filename=file_name
        ))
    table = '{agency}_metadata'.format(agency=agency)
    columns = (
        'created',
        'updated',
        'id',
        'json',
        'version_id'
    )
    bulk_save_agency(
        agency=agency,
        file_name=file_name,
        table=table,
        columns=columns,
        verbose=verbose
    )


def bulk_save_agency_pids(agency, file_name, verbose=False):
    """Bulk save agency data from pids table."""
    if verbose:
        click.echo('{agency} save to file: {filename}'.format(
            agency=agency,
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
    bulk_save_agency(
        agency=agency,
        file_name=tmp_file_name,
        table=table,
        columns=columns,
        verbose=verbose
    )
    # clean pid file
    with open(tmp_file_name, 'r') as file_in:
        with open(file_name, "w") as file_out:
            file_out.writelines(line for line in file_in if agency in line)
    os.remove(tmp_file_name)


def bulk_save_agency_ids(agency, file_name, verbose=False):
    """Bulk save agency data from id table."""
    if verbose:
        click.echo('{agency} save to file: {filename}'.format(
            agency=agency,
            filename=file_name
        ))
    table = '{agency}_id'.format(agency=agency)
    columns = ('recid', )
    bulk_save_agency(
        agency=agency,
        file_name=file_name,
        table=table,
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


def add_schema(record, agency):
    """Add the $schema to the record."""
    with current_app.app_context():
        schemas = current_app.config.get('RECORDS_JSON_SCHEMA')
        if agency in schemas:
            record['$schema'] = '{base_url}{endpoint}{schema}'.format(
                base_url=current_app.config.get('RERO_MEF_APP_BASE_URL'),
                endpoint=current_app.config.get('JSONSCHEMAS_ENDPOINT'),
                schema=schemas[agency]
            )
    return record


def create_agency_csv_file(input_file, agency, pidstore, metadata):
    """Create agency csv file to load."""
    if agency == 'mef':
        agency_id_file = open('{agency}_id'.format(agency=agency),
                              'w', encoding='utf-8')
    with \
            open(input_file, 'r', encoding='utf-8') as agency_file, \
            open(metadata, 'w', encoding='utf-8') as agency_metadata_file, \
            open(pidstore, 'w', encoding='utf-8') as agency_pids_file:

        for record in ijson.items(agency_file, "item"):
            if agency == 'viaf':
                record['pid'] = record['viaf_pid']

            ordered_record = add_md5(record)
            add_schema(ordered_record, agency)

            record_uuid = str(uuid4())
            date = str(datetime.utcnow())

            agency_metadata_file.write(
                metadata_csv_line(ordered_record, record_uuid, date)
            )

            agency_pids_file.write(
                pidstore_csv_line(agency, record['pid'], record_uuid, date)
            )
            if agency == 'mef':
                agency_id_file.write(record['pid'] + os.linesep)


def get_agency_classes():
    """Get agency classes from config."""
    agencies = {}
    endpoints = current_app.config.get('RECORDS_REST_ENDPOINTS', {})
    for agency in endpoints:
        record_class = obj_or_import_string(
            endpoints[agency].get('record_class', Record)
        )
        agencies[agency] = record_class
    return agencies


def get_agency_class(agency):
    """Get agency class from config."""
    agency_endpoint = current_app.config.get(
        'RECORDS_REST_ENDPOINTS', {}
    ).get(agency, {})
    record_class = obj_or_import_string(
        agency_endpoint.get('record_class', Record)
    )
    return record_class


def viaf_to_mef(viaf_record):
    """Transform viaf recod to mef."""
    mef_record = {}
    with current_app.app_context():
        agencies = get_agency_classes()
        agency_record = viaf_record
        viaf_pid = agency_record['viaf_pid']
        for key in agency_record:
            agency = key.split('_')[0]
            if agencies[agency].get_record_by_pid(agency_record[key]):
                add_agency_to_json(mef_record, agency, agency_record[key])
        if len(mef_record):
            add_schema(mef_record, 'mef')
            mef_record['viaf_pid'] = viaf_pid
    return mef_record


def write_link_json(
    agency,
    pidstore_file,
    metadata_file,
    viaf_pid,
    corresponding_data,
    agency_pid
):
    """Write a json record into file."""
    json_data = {}
    key_per_catalog_id = {
        'BNF': 'bnf_pid',
        'DNB': 'gnd_pid',
        'RERO': 'rero_pid',
        'SUDOC': 'idref_pid'
    }
    json_data['viaf_pid'] = viaf_pid
    write_to_file_viaf = False
    for catalog_id in corresponding_data:
        json_data[key_per_catalog_id[catalog_id]] = corresponding_data[
            catalog_id
        ]
        write_to_file_viaf = True
    write_to_file = False
    json_dump = json_data
    if agency == 'mef':
        json_dump = viaf_to_mef(json_data)
        if json_dump:
            json_dump['pid'] = agency_pid
            write_to_file = True
    else:
        agency_pid = viaf_pid
        add_schema(json_dump, 'viaf')
        json_dump['pid'] = agency_pid
        del(json_dump['viaf_pid'])
        # only save viaf data with used pids
        if agency == 'viaf':
            write_to_file = write_to_file_viaf
        else:
            write_to_file = True

    if write_to_file:
        record_uuid = str(uuid4())
        date = str(datetime.utcnow())
        pidstore_file.write(
            pidstore_csv_line(agency, agency_pid, record_uuid, date)
        )
        metadata_file.write(metadata_csv_line(json_dump, record_uuid, date))


def create_viaf_mef_files(
    agency,
    viaf_input_file,
    agency_pidstore_file_name,
    agency_metadata_file_name,
    verbose=False
):
    """Create agency csv file to load."""
    if verbose:
        click.echo('Start ***')

    agency_pid = 0
    corresponding_data = {}
    with open(
        agency_pidstore_file_name, 'w', encoding='utf-8'
    ) as agency_pidstore:
        with open(
            agency_metadata_file_name, 'w', encoding='utf-8'
        ) as agency_metadata:
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
                        agency_pid += 1
                        if verbose:
                            click.echo(
                                '{pid}: {viaf_pid} {corresponding}'.format(
                                    pid=agency_pid,
                                    viaf_pid=previous_viaf_pid,
                                    corresponding=corresponding_data
                                )
                            )
                        write_link_json(
                            agency,
                            agency_pidstore,
                            agency_metadata,
                            previous_viaf_pid,
                            corresponding_data,
                            str(agency_pid)
                        )
                        corresponding_data = {}
                        previous_viaf_pid = viaf_pid
                    corresponding = fields[1].split('|')
                    if len(corresponding) == 2:
                        corresponding_data[corresponding[0]] = corresponding[1]
                # save the last record
                agency_pid += 1
                if verbose:
                    click.echo(
                        '{pid}: {viaf_pid} {corresponding}'.format(
                            pid=agency_pid,
                            viaf_pid=previous_viaf_pid,
                            corresponding=corresponding_data
                        )
                    )
                write_link_json(
                    agency,
                    agency_pidstore,
                    agency_metadata,
                    previous_viaf_pid,
                    corresponding_data,
                    str(agency_pid)
                )


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
