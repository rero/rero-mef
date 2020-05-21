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
from copy import deepcopy
from datetime import datetime
from io import StringIO
from time import sleep
from uuid import uuid4

import click
import ijson
import psycopg2
import sqlalchemy
from flask import current_app
from invenio_db import db
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_rest.utils import obj_or_import_string
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


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
        with click.progressbar(items, length=length) as progressbar_items:
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


def get_record_class(agent):
    """Get the record class from agent.

    :param agent: agent to get class for
    :returns: record class for agent
    """
    # take the first defined doc type for finding the class
    record_class = obj_or_import_string(
        current_app.config.get('RECORDS_REST_ENDPOINTS').get(
            agent
        ).get('record_class', None)
    )
    return record_class


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
                        '{agency} copy from file: {count} {time}s'.format(
                            agency=agency,
                            count=count,
                            time=diff_time.seconds
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
                # gc.collect()
                # new buffer
                buffer = StringIO()

        if verbose:
            end_time = datetime.now()
            diff_time = end_time - start_time
            click.echo(
                '{agency} copy from file: {count} {time}s'.format(
                    agency=agency,
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


def get_agency_classes(without_mef_viaf=True):
    """Get agency classes from config."""
    agencies = {}
    endpoints = current_app.config.get('RECORDS_REST_ENDPOINTS', {})
    if without_mef_viaf:
        endpoints.pop('mef', None)
        endpoints.pop('viaf', None)
    for agency in endpoints:
        record_class = obj_or_import_string(
            endpoints[agency].get('record_class')
        )
        if record_class:
            agencies[agency] = record_class
    return agencies


def get_agency_class(agency):
    """Get agency class from config."""
    agency_endpoint = current_app.config.get(
        'RECORDS_REST_ENDPOINTS', {}
    ).get(agency, {})
    record_class = obj_or_import_string(
        agency_endpoint.get('record_class')
    )
    return record_class


def get_agency_search_class(agency):
    """Get agency search class from config."""
    agency_endpoint = current_app.config.get(
        'RECORDS_REST_ENDPOINTS', {}
    ).get(agency, {})
    search_class = obj_or_import_string(
        agency_endpoint.get('search_class')
    )
    return search_class


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
    for key, value in corresponding_data.items():
        if key in key_per_catalog_id:
            json_data[key_per_catalog_id[key]] = value
            write_to_file_viaf = True
    write_to_file = False
    json_dump = json_data

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
    agency_classes = get_agency_classes()
    viaf_agency_pid_names = {}
    for agency in agency_classes:
        viaf_agency_pid_names['{agency}_pid'.format(agency=agency)] = agency
        file_name = os.path.join(
            input_directory,
            '{agency}_pidstore.csv'.format(agency=agency)
        )
        if os.path.exists(file_name):
            if verbose:
                click.echo('  Read pids from: {name}'.format(name=file_name))
            length = number_records_in_file(file_name, 'csv')
            pids[agency] = {}
            progress = progressbar(
                items=open(file_name, 'r'),
                length=length,
                verbose=verbose
            )
            for line in progress:
                pid = line.split('\t')[3]
                pids[agency][pid] = 1

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
                    for pid_name, agency in viaf_agency_pid_names.items():
                        agency_pid = viaf_data.get(pid_name)
                        if agency_pid:
                            if pids.get(agency, {}).get(agency_pid):
                                corresponding_data['viaf_pid'] = viaf_pid
                                pids[agency].pop(agency_pid)
                                url = '{base_url}/api/{agency}/{pid}'.format(
                                    base_url=base_url,
                                    agency=agency,
                                    pid=agency_pid
                                )
                                corresponding_data[agency] = {'$ref': url}
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
                for agency in pids:
                    length += len(pids[agency])
                if verbose:
                    click.echo('  Create MEF without VIAF pid: {count}'.format(
                        count=length
                    ))
                progress = progressbar(
                    items=pids,
                    length=length,
                    verbose=verbose
                )
                for agency in progress:
                    url = '{base_url}/api/{agency}/{pid}'.format(
                        base_url=base_url,
                        agency=agency,
                        pid=pids[agency]
                    )
                    corresponding_data = {
                        'pid': str(mef_pid),
                        '$schema': schema,
                        'agency': url
                    }
                    mef_uuid = str(uuid4())
                    date = str(datetime.utcnow())
                    mef_pidstore.write(
                        pidstore_csv_line('mef', str(mef_pid), mef_uuid, date)
                    )
                    mef_metadata.write(
                        metadata_csv_line(corresponding_data, mef_uuid, date)
                    )
                    mef_ids_file.write(str(mef_pid) + os.linesep)
                    mef_pid += 1
    if verbose:
        click.echo('  MEF records created: {count}'.format(count=mef_pid-1))


def create_viaf_files(
    agency,
    viaf_input_file,
    viaf_pidstore_file_name,
    viaf_metadata_file_name,
    verbose=False
):
    """Create VIAF csv file to load."""
    if verbose:
        click.echo('Start ***')

    agency_pid = 0
    corresponding_data = {}
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
                            viaf_pidstore,
                            viaf_metadata,
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
                    viaf_pidstore,
                    viaf_metadata,
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


def get_agencies_endpoints(without_mef_viaf=True):
    """Get all agencies from config."""
    agencies = deepcopy(current_app.config.get('RECORDS_REST_ENDPOINTS', {}))
    if without_mef_viaf:
        agencies.pop('mef', None)
        agencies.pop('viaf', None)
    return agencies


def get_diff_db_es_pids(agency, verbose=False):
    """Get differences between DB and ES pids."""
    pids_db = {}
    pids_es = {}
    pids_es_double = []
    record_class = get_agency_class(agency)
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
    search_class = get_agency_search_class(agency)
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
