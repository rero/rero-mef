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

"""Click command-line interface for MEF record management."""

from __future__ import absolute_import, print_function

import copy
import json
import sys

import click
from flask import current_app
from flask.cli import with_appcontext
from invenio_indexer.cli import index

from .authorities.marctojson.records import RecordsCount
from .authorities.models import AgencyAction
from .authorities.utils import add_md5_to_json, bulk_load_agency_metadata, \
    bulk_load_agency_pids, create_agency_csv_file, create_viaf_mef_files, \
    index_agency


@click.group()
def fixtures():
    """Fixtures management commands."""


@fixtures.command('create_or_update')
@click.argument('agency')
@click.argument('source', type=click.File('r'), default=sys.stdin)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def create_or_update(agency, source, verbose):
    """Create or update authority person records."""
    agency_message = 'Update authority person records: {agency}'.format(
        agency=agency
    )
    click.secho(agency_message, fg='green')
    data = json.load(source)

    if isinstance(data, dict):
        data = [data]

    with current_app.app_context():
        agencies = current_app.config.get('AGENCIES')
        for record in data:
            returned_record, status = agencies[agency].create_or_update(
                record, agency=agency, dbcommit=True, reindex=True
            )
            if status != AgencyAction.DISCARD:
                id_type = ' record uuid: '
                id = returned_record.id
            else:
                id = record['pid']
                id_type = ' record pid : '

            message_str = {
                'agency': agency,
                'id_type': id_type,
                'id': id,
                'separator': ' | ',
                'status': status,
            }
            message = '{agency}{id_type}{id}{separator}{status}'.format(
                **message_str
            )
            click.echo(message)


def marc_to_json(agency, marc_file, json_file, verbose):
    """Marc to JSON conversion."""
    with current_app.app_context():
        transformation = current_app.config.get('TRANSFORMATION')
        records = []
        try:
            records = RecordsCount(str(marc_file))
        except Exception as error:
            agency_message = 'Marc file not found for {ag}:{err}'.format(
                ag=agency, err=error
            )
            click.secho(agency_message, fg='red', err=True)

        if json_file:
            json_file = open(json_file, 'w', encoding='utf8')
        else:
            json_file = sys.stdout

        json_file.write('[\n')
        for record, count in records:
            if (
                (agency == 'bnf' and not record.get_fields('200')) or
                (agency == 'gnd' and not record.get_fields('100')) or
                (agency == 'rero' and not record.get_fields('100'))
            ):
                pass
            else:
                if count > 1:
                    json_file.write(',\n')

                data = transformation[agency](marc=record)
                add_md5_to_json(data.json)
                json.dump(data.json, json_file, ensure_ascii=False, indent=2)
        json_file.write('\n]\n')


def agency_membership(params):
    """Check if agency is previously configured."""
    agency = params['agency']
    params['agency_is_source'] = False
    params['agency_is_member'] = False
    with current_app.app_context():
        all_agencies = current_app.config.get('AGENCIES')
        if agency in all_agencies:
            params['agency_is_member'] = True
        agencies = copy.deepcopy(all_agencies)
        del agencies['viaf']
        del agencies['mef']
        if agency in agencies:
            params['agency_is_source'] = True


def marctojson_action(params):
    """Check if marc to json transformation is required."""
    params['marctojson'] = False
    if (
        params['agency_is_source'] and
        params['marc_file'] and params['json_file']
    ):
        params['marctojson'] = True


def csv_action(params):
    """Check if json to csv transformation is required."""
    params['csv_action'] = False
    if (
        params['agency_is_member'] and
        not params['agency_is_source'] and
        params['json_file'] and
        params['csv_pidstore_file'] and
        params['csv_metadata_file'] and
        params['rero_pids']
    ):
        params['csv_action'] = True
    elif (
        params['agency_is_member'] and
        params['agency_is_source'] and
        params['json_file'] and
        params['csv_pidstore_file'] and
        params['csv_metadata_file']
    ):
        params['csv_action'] = True


def db_action(params):
    """Check if db load is required."""
    params['db_action'] = False
    if (
        params['agency_is_member'] and
        params['csv_pidstore_file'] and
        params['csv_metadata_file'] and
        params['load_records']
    ):
        params['db_action'] = True


def valid_agency(params):
    """Check ageny is valid."""
    if 'agency' in params:
        params['valid'] = True
    else:
        params['valid'] = False


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


@fixtures.command('bulk_load')
@click.argument('agency')
@click.option(
    '-m', '--marc_file', 'marc_file', help='MARC file to transform to JSON .'
)
@click.option('-j', '--json_file', 'json_file', help='JSON: output file.')
@click.option(
    '-s',
    '--csv_pidstore_file',
    'csv_pidstore_file',
    help='pidstore: CSV output file.',
)
@click.option(
    '-d',
    '--csv_metadata_file',
    'csv_metadata_file',
    help='metadata: CSV output file.',
)
@click.option(
    '-p',
    '--rero_pids',
    'rero_pids',
    help='rero pids: tab delemited file of rero ids.',
)
@click.option(
    '-l',
    '--load_records',
    'load_records',
    help='To load csv files to database.',
    is_flag=True, default=False
)
@click.argument('input_directory')
@click.argument('output_directory')
@click.option(
    '-c',
    '--bulk_count',
    'bulkcount',
    help='Set the bulk load chunk size.',
    default=0,
    type=int
)
@click.option('-r', '--reindex', 'reindex', help='add record to reindex.',
              is_flag=True, default=False)
@click.option('-P', '--process', 'process', help='process reindex.',
              is_flag=True, default=False)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def bulk_load(
    **kwargs
):
    """Agency record management."""
    params = kwargs
    valid_agency(params)
    agency_membership(params)
    marctojson_action(params)
    csv_action(params)
    db_action(params)
    agency = params['agency']
    verbose = params['verbose']
    reindex = params['reindex']
    process = params['process']
    if params['bulkcount'] > 0:
        bulk_count = params['bulkcount']
    else:
        bulk_count = current_app.config.get('BULK_CHUNK_COUNT', 100000)

    input_directory = params['input_directory']
    output_directory = params['output_directory']

    message = ' Tasks for agency: {agency}'.format(agency=agency)
    click.secho(message, err=True)

    if 'marctojson' in params and params['marctojson']:
        message = '  Transform MARC to JSON. '.format()
        click.secho(message, err=True)
        marc_file = '{dir}/{file}'.format(
            dir=input_directory, file=params['marc_file'])
        json_file = '{dir}/{file}'.format(
            dir=output_directory, file=params['json_file'])

        marc_to_json(agency, marc_file, json_file, verbose)

        message = '  Number of JSON records created: {number}. '.format(
            number=number_records_in_file(json_file, 'json'))
        click.secho(message, fg='green', err=True)

    if 'csv_action' in params and params['csv_action']:
        message = '  Create CSV files from JSON. '.format()
        click.secho(message, err=True)
        json_file = '{dir}/{file}'.format(
            dir=input_directory, file=params['json_file'])
        pidstore = '{dir}/{file}'.format(
            dir=output_directory, file=params['csv_pidstore_file'])
        metadata = '{dir}/{file}'.format(
            dir=output_directory, file=params['csv_metadata_file'])
        message = '  JSON input file: {file} '.format(file=json_file)
        click.secho(message, err=True)
        message = '  CSV output files: {pidstore}, {metadata} '.format(
            pidstore=pidstore, metadata=metadata)
        click.secho(message, err=True)

        if params['agency_is_source']:
            create_agency_csv_file(json_file, agency, pidstore, metadata)
        else:
            rero_pids = '{dir}/{file}'.format(
                dir=input_directory, file=params['rero_pids'])
            create_viaf_mef_files(agency, rero_pids, json_file, pidstore,
                                  metadata, verbose)

        message = '  Number of records created in pidstore: {number}. '.format(
            number=number_records_in_file(pidstore, 'csv'))
        click.secho(message, fg='green', err=True)
        message = '  Number of records created in metadata: {number}. '.format(
            number=number_records_in_file(metadata, 'csv'))
        click.secho(message, fg='green', err=True)

    if 'db_action' in params and params['db_action']:
        message = '  Load CSV files into database. '.format()
        click.secho(message, err=True)
        pidstore = '{dir}/{file}'.format(
            dir=input_directory, file=params['csv_pidstore_file'])
        metadata = '{dir}/{file}'.format(
            dir=input_directory, file=params['csv_metadata_file'])
        message = '  CSV input files: {pidstore}|{metadata} '.format(
            pidstore=pidstore, metadata=metadata)
        click.secho(message, err=True)

        message = '  Number of records in pidstore to load: {number}. '.format(
            number=number_records_in_file(pidstore, 'csv'))
        click.secho(message, fg='green', err=True)

        bulk_load_agency_pids(agency, pidstore,  bulk_count=bulk_count,
                              verbose=verbose)

        message = '  Number of records in metadata to load: {number}. '.format(
            number=number_records_in_file(metadata, 'csv'))
        click.secho(message, fg='green', err=True)

        bulk_load_agency_metadata(agency, metadata, bulk_count=bulk_count,
                                  verbose=verbose,
                                  reindex=reindex,  process=process)


@index.command('agency')
@click.argument('agency')
@click.option('-k', '--enqueue', is_flag=True, default=False,
              help='Enqueue indexing and return immediately.')
@click.option('-c', '--chunksize', 'chunksize', help='Set the chunk size.',
              default=100000, type=int)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def indexagency(agency, chunksize, enqueue, verbose):
    """Index agency records."""
    message = 'Index records: {agency}'.format(
        agency=agency
    )
    click.secho(message, fg='green')
    index_agency(agency=agency, chunksize=chunksize,
                 enqueue=enqueue, verbose=verbose)
