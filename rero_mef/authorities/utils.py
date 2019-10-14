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
from flask import current_app
from invenio_indexer.api import RecordIndexer
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine

from .api import MefRecord


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
    ref_string = MefRecord.build_ref_string(
        agency=agency, agency_pid=agency_pid
    )
    mef_record[agency] = {'$ref': ref_string}


def raw_connection():
    """Return a raw connection to the database."""
    with current_app.app_context():
        URI = current_app.config.get('SQLALCHEMY_DATABASE_URI')
        engine = create_engine(URI)
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
        current_app.logger.error(
            'data load error: {0}'.format(error)
        )
    cursor.execute('VACUUM ANALYSE {table}'.format(table=table))
    cursor.close()
    connection.close()


def bulk_index(uuids, agency, process=False, verbose=False):
    """Bulk index records."""
    if verbose:
        click.echo(' add to index: {count}'.format(count=len(uuids)))
    indexer = RecordIndexer()
    retry = True
    minutes = 1
    while retry:
        try:
            indexer.bulk_index(uuids)
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
    if process:
        indexer.process_bulk_queue()


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
                     reindex=False, process=False):
    """Bulk load agency data to table."""
    # print_memory(verbose, 'Start {agency}'.format(agency=agency))
    if bulk_count <= 0:
        bulk_count = current_app.config.get('BULK_CHUNK_COUNT', 100000)
    count = 0
    buffer = StringIO()
    buffer_uuid = []
    if 'id' in columns:
        index = columns.index('id')
    else:
        index = -1
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
                db_copy_from(
                    buffer=buffer,
                    table=table,
                    columns=columns
                )
                buffer.close()

                if index >= 0 and reindex:
                    bulk_index(
                        agency=agency,
                        uuids=buffer_uuid,
                        process=process,
                        verbose=verbose
                    )
                else:
                    if verbose:
                        click.echo()
                buffer_uuid.clear()
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
        db_copy_from(
            buffer=buffer,
            table=table,
            columns=columns
        )
        buffer.close()
        if index >= 0 and reindex:
            bulk_index(
                agency=agency,
                uuids=buffer_uuid,
                process=process,
                verbose=verbose
            )
        else:
            if verbose:
                click.echo()
        buffer_uuid.clear()

    # force the Garbage Collector to release unreferenced memory
    gc.collect()
    # print_memory(verbose, 'End {agency}'.format(agency=agency))


def bulk_load_agency_metadata(agency, metadata, bulk_count=0,
                              verbose=True, reindex=False, process=False):
    """Bulk load agency data to metadata table."""
    table = 'records_metadata'
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
        reindex=reindex,
        process=process
    )


def bulk_load_agency_pids(agency, pidstore, bulk_count=0,
                          verbose=True, reindex=False, process=False):
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
        reindex=reindex,
        process=process
    )


def add_md5_to_json(record):
    """Add md5 to json."""
    data_md5 = hashlib.md5(
        json.dumps(record, sort_keys=True).encode('utf-8')
    ).hexdigest()
    record['md5'] = data_md5
    return record


def add_schema(record, agency):
    """Add the $schema to the record."""
    with current_app.app_context():
        s_data = {
            'http': 'http://',
            'url': current_app.config.get('JSONSCHEMAS_HOST'),
            'schema': '/schemas/authorities/',
            'agency': agency,
            'suffix': '-person-v0.0.1.json',
        }
        schema_str = '{http}{url}{schema}{agency}{suffix}'.format(**s_data)
        record['$schema'] = schema_str


def create_agency_csv_file(input_file, agency, pidstore, metadata):
    """Create agency csv file to load."""
    with \
            open(input_file, 'r', encoding='utf-8') as agency_file, \
            open(metadata, 'w', encoding='utf-8') as agency_metadata_file, \
            open(pidstore, 'w', encoding='utf-8') as agency_pids_file:

        for record in ijson.items(agency_file, "item"):
            if agency == 'viaf':
                record['pid'] = record['viaf_pid']

            ordered_record = add_md5_to_json(record)
            add_schema(ordered_record, agency)

            record_uuid = str(uuid4())
            date = str(datetime.utcnow())

            agency_metadata_file.write(
                metadata_csv_line(ordered_record, record_uuid, date)
            )

            agency_pids_file.write(
                pidstore_csv_line(agency, record['pid'], record_uuid, date)
            )


def viaf_to_mef(viaf_record):
    """Transform viaf recod to mef."""
    mef_record = {}
    with current_app.app_context():
        agencies = current_app.config.get('AGENCIES')
        agency_record = viaf_record
        viaf_pid = agency_record['viaf_pid']
        for key in agency_record:
            agency = key[:-4]
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
    }
    json_data['viaf_pid'] = viaf_pid
    for catalog_id in corresponding_data:
        json_data[key_per_catalog_id[catalog_id]] = corresponding_data[
            catalog_id
        ]
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
    rero_pids_file,
    viaf_input_file,
    agency_pidstore_file_name,
    agency_metadata_file_name,
    verbose=False
):
    """Create agency csv file to load."""
    with open(rero_pids_file, 'r', encoding='utf-8', buffering=1) as rero_pids:
        if verbose:
            click.echo(
                'Read from file: {filename}'.format(filename=rero_pids_file)
            )
        rero_id_control_number = {}
        for line in rero_pids:
            parts = line.rstrip().split('\t')
            rero_id_control_number[parts[0]] = parts[1]
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
                        if corresponding[0] in ['BNF', 'DNB']:
                            corresponding_data[corresponding[0]] = \
                                corresponding[1]
                        elif corresponding[0] == 'RERO':
                            # corresponding_data['VIRTUA'] = corresponding[1]
                            if corresponding[1] in rero_id_control_number:
                                corresponding_data[
                                    'RERO'
                                ] = rero_id_control_number[corresponding[1]]
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
