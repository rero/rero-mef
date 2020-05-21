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
import itertools
import json
import os
import sys
from time import sleep

import click
import redis
import yaml
from celery.task.control import inspect
from flask import current_app
from flask.cli import with_appcontext
from invenio_oaiharvester.cli import oaiharvester
from invenio_oaiharvester.models import OAIHarvestConfig
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.api import Record
from invenio_records_rest.utils import obj_or_import_string

from rero_mef.tasks import process_bulk_queue

from .authorities.api import AuthRecordIndexer
from .authorities.marctojson.helper import nice_record
from .authorities.marctojson.records import RecordsCount
from .authorities.mef.api import MefRecord
from .authorities.mef.models import MefIdentifier
from .authorities.tasks import \
    create_mef_and_agencies_from_viaf as task_mef_and_agencies_from_viaf
from .authorities.tasks import create_mef_from_agency as task_mef_from_agency
from .authorities.tasks import create_or_update as task_create_or_update
from .authorities.tasks import delete as task_delete
from .authorities.utils import add_md5, append_fixtures_new_identifiers, \
    bulk_load_agency_ids, bulk_load_agency_metadata, bulk_load_agency_pids, \
    bulk_save_agency_ids, bulk_save_agency_metadata, bulk_save_agency_pids, \
    create_agency_csv_file, create_mef_files, create_viaf_files, \
    get_agencies_endpoints, get_agency_class, get_agency_classes, \
    get_agency_search_class, number_records_in_file, progressbar
from .authorities.viaf.api import ViafRecord, ViafSearch
from .utils import add_oai_source, oai_get_last_run, oai_set_last_run, \
    read_json_record


def abort_if_false(ctx, param, value):
    """Abort command is value is False."""
    if not value:
        ctx.abort()


@click.group()
def fixtures():
    """Fixtures management commands."""


@click.group()
def utils():
    """Misc management commands."""


@click.group()
def celery():
    """Celery management commands."""


@fixtures.command('create_or_update')
@click.argument('agency')
@click.argument('source', type=click.File('r'), default=sys.stdin)
@click.option('-l', '--lazy', 'lazy', is_flag=True, default=False)
@click.option('-5', '--md5', 'test_md5', is_flag=True, default=False,
              help='Compaire md5 to find out if we have to update')
@click.option('-k', '--enqueue', 'enqueue', is_flag=True, default=False,
              help="Enqueue record creation.")
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def create_or_update(agency, source, lazy, test_md5, enqueue, verbose):
    """Create or update authority person records.

    :param agency: Agency to create or update.
    :param source: File with agencies data in json format.
    :param lazy: lazy reads file
    :param test_md5: Compaire md5 to find out if we have to update.
    :param verbose: Verbose.
    """
    agency_message = 'Update authority person records: {agency}'.format(
        agency=agency
    )
    click.secho(agency_message, fg='green')
    if lazy:
        # try to lazy read json file (slower, better memory management)
        data = read_json_record(source)
    else:
        data = json.load(source)
        if isinstance(data, dict):
            data = [data]

    for count, record in enumerate(data):
        if enqueue:
            task_create_or_update.delay(
                index=count,
                record=record,
                agency=agency,
                dbcommit=True,
                reindex=True,
                test_md5=test_md5,
                verbose=verbose
            )
        else:
            id_type, id, agency_action, mef_action = task_create_or_update(
                index=count,
                record=record,
                agency=agency,
                dbcommit=True,
                reindex=True,
                test_md5=test_md5,
                verbose=verbose
            )
        if verbose:
            message = '{count:<10} {agency}'.format(
                count=count,
                agency=agency,
            )
            if not enqueue:
                message += ' {type}{id:<38}' \
                           ' | {agency_action} | {mef_action}'.format(
                                type=id_type,
                                id=id,
                                agency_action=agency_action,
                                mef_action=mef_action
                           )
            click.echo(message)


@fixtures.command('delete')
@click.argument('agency')
@click.argument('source', type=click.File('r'), default=sys.stdin)
@click.option('-l', '--lazy', 'lazy', is_flag=True, default=False)
@click.option('-k', '--enqueue', 'enqueue', is_flag=True, default=False,
              help="Enqueue record deletion.")
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def delete(agency, source, lazy, enqueue, verbose):
    """Delete authority person records.

    :param agency: Agency to create or update.
    :param source: File with agencies data in json format.
    :param lazy: lazy reads file
    :param verbose: Verbose.
    """
    agency_message = 'Delete authority person records: {agency}'.format(
        agency=agency
    )
    click.secho(agency_message, fg='green')
    if lazy:
        # try to lazy read json file (slower, better memory management)
        data = read_json_record(source)
    else:
        data = json.load(source)
        if isinstance(data, dict):
            data = [data]

    for count, record in enumerate(data):
        if enqueue:
            msg = task_delete.delay(
                index=count,
                pid=record.get('pid'),
                agency=agency,
                dbcommit=True,
                delindex=True,
                verbose=verbose
            )
        else:
            msg = task_delete(
                index=count,
                pid=record.get('pid'),
                agency=agency,
                dbcommit=True,
                delindex=True,
                verbose=verbose
            )
        if verbose:
            message = '{count:<10} {agency}: {pid}\t{msg}'.format(
                count=count,
                agency=agency,
                pid=record.get('pid'),
                msg=msg
            )
            click.echo(message)
    if agency == 'viaf':
        if enqueue:
            wait_empty_tasks(delay=3, verbose=True)
        count = 0
        for pid in MefRecord.get_all_empty_pids():
            count += 1
            mef_record = MefRecord.get_record_by_pid(pid)
            mef_record.delete(dbcommit=True, delindex=True)
        click.secho(
            'Mef records deleted: {count}'.format(count=count),
            fg='yellow'
        )


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
        not_first_line = False
        pids = {}
        for record, count in records:
            data = transformation[agency](marc=record)
            if data:
                pid = data.json.get('pid')
                if pids.get(pid):
                    click.secho(
                        '  Error duplicate pid in {agency}: {pid}'.format(
                            agency=agency,
                            pid=pid
                        ),
                        fg='red'
                    )
                else:
                    if not_first_line:
                        json_file.write(',\n')
                    pids[pid] = 1
                    add_md5(data.json)
                    json.dump(data.json, json_file, ensure_ascii=False,
                              indent=2)
                    not_first_line = True
            else:
                click.secho(
                    '  Error can not transform marc in {agency}: {rec}'.format(
                        agency=agency,
                        rec=nice_record(record)
                    ),
                    fg='yellow'
                )
        json_file.write('\n]\n')


def agency_membership(params):
    """Check if agency is previously configured."""
    agency = params['agency']
    params['agency_is_source'] = False
    params['agency_is_member'] = False
    with current_app.app_context():
        all_agencies = get_agency_classes(without_mef_viaf=False)
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
        params['csv_metadata_file']
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
    """Check agency is valid."""
    if 'agency' in params:
        params['valid'] = True
    else:
        params['valid'] = False


@fixtures.command('bulk_load')
@click.argument('agency')
@click.argument('input_directory')
@click.argument('output_directory')
@click.option('-m', '--marc_file', 'marc_file',
              help='MARC file to transform to JSON .')
@click.option('-j', '--json_file', 'json_file', help='JSON: output file.')
@click.option('-s', '--csv_pidstore_file', 'csv_pidstore_file',
              help='pidstore: CSV output file.')
@click.option('-d', '--csv_metadata_file', 'csv_metadata_file',
              help='metadata: CSV output file.')
@click.option('-l', '--load_records', 'load_records', is_flag=True,
              default=False, help='To load csv files to database.')
@click.option('-c' '--bulk_count', 'bulkcount', default=0, type=int,
              help='Set the bulk load chunk size.')
@click.option('-r', '--reindex', 'reindex', help='add record to reindex.',
              is_flag=True, default=False)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def bulk_load(**kwargs):
    """Agency record management.

    :param marc_file: MARC file to transform to JSON .
    :param json_file: JSON: output file.
    :param csv_pidstore_file: pidstore: CSV output file.
    :param csv_metadata_file: metadata: CSV output file.
    :param load_records: To load csv files to database.
    :param bulk_count: Set the bulk load chunk size.
    :param reindex: add record to reindex.
    :param verbose: Verbose.
    """
    params = kwargs
    valid_agency(params)
    agency_membership(params)
    marctojson_action(params)
    csv_action(params)
    db_action(params)
    agency = params['agency']
    verbose = params['verbose']
    reindex = params['reindex']
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
        message = '  CSV output files: {pidstore}, {metadata}'.format(
            pidstore=pidstore, metadata=metadata)
        if agency == 'mef':
            ids = os.path.join(output_directory, 'mef_id.csv')
            message += ', {ids}'.format(ids=ids)
        click.secho(message, err=True)

        if params['agency_is_source']:
            create_agency_csv_file(json_file, agency, pidstore, metadata)
        else:
            if agency == 'viaf':
                create_viaf_files(
                    agency=agency,
                    viaf_input_file=json_file,
                    viaf_pidstore_file_name=pidstore,
                    viaf_metadata_file_name=metadata,
                    verbose=verbose
                )
            elif agency == 'mef':
                create_mef_files(
                    viaf_pidstore_file=json_file,
                    input_directory=input_directory,
                    mef_pidstore_file_name=pidstore,
                    mef_metadata_file_name=metadata,
                    mef_ids_file_name=ids,
                    verbose=verbose
                )
        message = '  Number of records created in pidstore: {number}. '.format(
            number=number_records_in_file(pidstore, 'csv'))
        click.secho(message, fg='green', err=True)
        message = '  Number of records created in metadata: {number}. '.format(
            number=number_records_in_file(metadata, 'csv'))
        click.secho(message, fg='green', err=True)
        if agency == 'mef':
            message = '  Number of records created in ids: {number}. '.format(
                number=number_records_in_file(ids, 'csv'))
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

        bulk_load_agency_pids(agency, pidstore, bulk_count=bulk_count,
                              verbose=verbose)

        message = '  Number of records in metadata to load: {number}. '.format(
            number=number_records_in_file(metadata, 'csv'))
        click.secho(message, fg='green', err=True)

        bulk_load_agency_metadata(agency, metadata, bulk_count=bulk_count,
                                  verbose=verbose, reindex=reindex)
        if agency == 'mef':
            ids_file_name = '{dir}/{agency}_id.csv'.format(
                dir=input_directory, agency=agency)
            if os.path.exists(ids_file_name):
                message = '  {msg}: {number}. '.format(
                    msg='Number of records in id to load: {number}',
                    number=number_records_in_file(ids_file_name, 'csv'))
                click.secho(message, fg='green', err=True)

                bulk_load_agency_ids(agency, ids_file_name,
                                     bulk_count=bulk_count,
                                     verbose=verbose)
                append_fixtures_new_identifiers(MefIdentifier, [], 'mef')
        # set last run if file exist
        file_name = os.path.join(
            output_directory,
            '{agency}_last_run.txt'.format(agency=agency)
        )
        try:
            with open(file_name) as last_run_file:
                last_run = last_run_file.readline()
                if verbose:
                    click.secho(
                        '  Set last run: {lastrun}'.format(lastrun=last_run),
                        fg='green'
                    )
                oai_set_last_run(agency, last_run)
        except Exception as err:
            pass


@fixtures.command('bulk_save')
@click.argument('output_directory')
@click.option('-a', '--agencies', 'agencies', multiple=True,
              default=['bnf', 'gnd', 'idref', 'rero', 'mef', 'viaf'])
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def bulk_save(agencies, output_directory, verbose):
    """Agencies record dump.

    :param agencies: Agencies to export.
        default=['bnf', 'gnd', 'idref', 'rero', 'mef', 'viaf'])
    :param verbose: Verbose.
    """
    for agency in agencies:
        click.secho(
            'Save {agency} CSV files to directory: {path}'.format(
                agency=agency,
                path=output_directory,
            ),
            fg='green'
        )
        file_name = os.path.join(
            output_directory,
            '{agency}_metadata.csv'.format(agency=agency)
        )
        if verbose:
            click.echo(
                '  Save metadata: {file_name}'.format(file_name=file_name))
        bulk_save_agency_metadata(agency, file_name=file_name, verbose=False)
        file_name = os.path.join(
            output_directory,
            '{agency}_pidstore.csv'.format(agency=agency)
        )
        if verbose:
            click.echo(
                '  Save pidstore: {file_name}'.format(file_name=file_name))
        bulk_save_agency_pids(agency, file_name=file_name, verbose=False)
        if agency == 'mef':
            file_name = os.path.join(
                output_directory,
                '{agency}_id.csv'.format(agency=agency)
            )
            if verbose:
                click.echo(
                    '  Save id: {file_name}'.format(file_name=file_name))
            bulk_save_agency_ids(agency, file_name=file_name, verbose=False)
        last_run = oai_get_last_run(agency)
        if last_run:
            file_name = os.path.join(
                output_directory,
                '{agency}_last_run.txt'.format(agency=agency)
            )
            if verbose:
                click.echo(
                    '  Save last run: {file_name}'.format(file_name=file_name))
            with open(file_name, 'w') as last_run_file:
                last_run_file.write('{lastrun}'.format(lastrun=last_run))


@fixtures.command('csv_to_json')
@click.argument('csv_metadata_file')
@click.argument('json_output_file')
@click.option('-I', '--indent', 'indent', type=click.INT, default=2)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def csv_to_json(csv_metadata_file, json_output_file, indent, verbose):
    """Agencies record dump.

    :param csv_metadata_file: csv metadata file.
    :param json_output_file: json output file.
    :param indent: indent for output
    :param verbose: Verbose.
    """
    click.secho(
        'CSV to json transform: {meta} -> {json}'.format(
            meta=csv_metadata_file,
            json=json_output_file
        ),
        fg='green'
    )
    output = '['
    offset = '{character:{indent}}'.format(character=' ', indent=indent)
    with open(csv_metadata_file) as metadata_file:
        with open(json_output_file, 'w') as output_file:
            count = 0
            for metadata_line in metadata_file:
                count += 1
                output_file.write(output)
                if count > 1:
                    output_file.write(',')
                data = json.loads(metadata_line.split('\t')[3])
                if verbose:
                    click.echo('{count:<10}: {pid}\t{data}'.format(
                        count=count,
                        pid=data['pid'],
                        data=data
                    ))

                output = ''
                lines = json.dumps(data, indent=indent).split('\n')
                for line in lines:
                    output += '\n{offset}{line}'.format(
                        offset=offset,
                        line=line
                    )
            output_file.write(output)
            output_file.write('\n]\n')


@fixtures.command('csv_diff')
@click.argument('csv_metadata_file')
@click.option('-c', '-csv_metadata_file_compair', 'csv_metadata_file_compair',
              default=None)
@click.option('-a', '--agent', 'agent', default=None)
@click.option('-o', '--output', 'output', is_flag=True, default=False)
@click.option('-I', '--indent', 'indent', type=click.INT, default=2)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def csv_diff(csv_metadata_file, csv_metadata_file_compair, agent, output,
             indent, verbose, ):
    """Agencies record diff.

    :param csv_metadata_file: csv metadata file to compair.
    :param csv_metadata_file_compair: csv metadata file to compair too.
    :param agent: agent type to compair too.
    :param verbose: Verbose.
    """
    def get_pid_data(line):
        """Get json from CSV text line.

        :param line: line of CSV text.
        :returns: data as json
        """
        data = json.loads(line.split('\t')[3])
        pid = data.get('pid')
        return pid, data

    def ordert_data(data):
        """Order data pid, .

        :param line: line of CSV text.
        :returns: data as json
        """
        data = json.loads(data.split('\t')[3])
        pid = data.get('pid')
        return pid, data

    offset = '{character:{indent}}'.format(character=' ', indent=indent)

    def intent_output(data, intent):
        """Creates intented output.

        :param data: data to output.
        :param intent: intent to use.
        :returns: intented data.
        """
        output = ''
        lines = json.dumps(data, indent=indent).split('\n')
        for line in lines:
            output += '\n{offset}{line}'.format(offset=offset, line=line)
        return output

    if csv_metadata_file_compair and not agent:
        compair = csv_metadata_file_compair
    elif agent:
        compair = agent
    else:
        click.secho('One of -a or -d parameter mandatory', fg='red')
        sys.exit(1)
    click.secho(
        'CSV diff: {first} <-> {second}'.format(
            first=compair,
            second=csv_metadata_file
        ),
        fg='green'
    )
    if output:
        file_name = os.path.splitext(csv_metadata_file)[0]
        file_name_new = '{name}_new.json'.format(name=file_name)
        file_new = open(file_name_new, 'w')
        file_new.write('[')
        file_name_diff = '{name}_changed.json'.format(name=file_name)
        file_diff = open(file_name_diff, 'w')
        file_diff.write('[')
        file_name_delete = '{name}_delete.json'.format(name=file_name)
        file_delete = open(file_name_delete, 'w')
        file_delete.write('[')
        click.echo('New     file: {name}'.format(name=file_name_new))
        click.echo('Changed file: {name}'.format(name=file_name_diff))
        click.echo('Deleted file: {name}'.format(name=file_name_delete))

    compaire_data = {}
    length = number_records_in_file(csv_metadata_file_compair, 'csv')
    if csv_metadata_file_compair and not agent:
        with open(csv_metadata_file_compair, 'r', buffering=1) as meta_file:
            label = 'Loading: {name}'.format(name=compair)
            with click.progressbar(meta_file, length=length,
                                   label=label) as metadata:
                for metadata_line in metadata:
                    pid, data = get_pid_data(metadata_line)
                    compaire_data[pid] = data
    elif agent:
        agent_class = get_agency_class(agent)
        length = agent_class.count()
        ids = agent_class.get_all_ids()
        with click.progressbar(ids, length=length) as record_ids:
            for id in record_ids:
                record = agent_class.get_record_by_id(id)
                pid = record.pid
                compaire_data[pid] = record

    with open(csv_metadata_file, 'r', buffering=1) as metadata_file:
        for metadata_line in metadata_file:
            pid, data = get_pid_data(metadata_line)
            if pid in compaire_data:
                if compaire_data[pid] != data:
                    click.echo('DIFF: ')
                    click.echo(' old:\t{data}'.format(
                        data=json.dumps(compaire_data[pid], sort_keys=True)
                    ))
                    click.echo(' new:\t{data}'.format(
                        data=json.dumps(data, sort_keys=True)
                    ))
                    if output:
                        file_diff.write(intent_output(data, indent))
                del(compaire_data[pid])
            else:
                click.echo('NEW :\t{data}'.format(
                    data=json.dumps(data, sort_keys=True)
                ))
                if output:
                    file_new.write(intent_output(data, indent))
    for pid, data in compaire_data.items():
        click.echo('DEL :\t{data}'.format(
            data=json.dumps(data, sort_keys=True)
        ))
        if output:
            file_delete.write(intent_output(data, indent))

    if output:
        file_new.write(']')
        file_new.close()
        file_diff.write(']')
        file_diff.close()
        file_delete.write(']')
        file_delete.close()
    sys.exit(0)


@oaiharvester.command('addsource')
@click.argument('name')
@click.argument('baseurl')
@click.option('-m', '--metadataprefix', default='marc21',
              help='The prefix for the metadata')
@click.option('-s', '--setspecs', default='',
              help='The ‘set’ criteria for the harvesting')
@click.option('-c', '--comment', default='', help='Comment')
@with_appcontext
def add_oai_source_config(name, baseurl, metadataprefix, setspecs, comment):
    """Add OAIHarvestConfig.

    :param name: Name of OAI source.
    :param baseurl: Baseurl of OAI source.
    :param metadataprefix: The prefix for the metadata
    :param setspecs: The `set` criteria for the harvesting
    :param comment: Comment
    """
    click.echo('Add OAIHarvestConfig: {0} '.format(name), nl=False)
    if add_oai_source(name=name, baseurl=baseurl,
                      metadataprefix=metadataprefix, setspecs=setspecs,
                      comment=comment):
        click.secho('Ok', fg='green')
    else:
        click.secho('Exist', fg='red')


@oaiharvester.command('initconfig')
@click.argument('configfile', type=click.File('rb'))
@with_appcontext
def init_oai_harvest_config(configfile):
    """Init OAIHarvestConfig."""
    configs = yaml.load(configfile)
    for name, values in sorted(configs.items()):
        baseurl = values['baseurl']
        metadataprefix = values.get('metadataprefix', 'marc21')
        setspecs = values.get('setspecs', '')
        comment = values.get('comment', '')
        click.echo(
            'Add OAIHarvestConfig: {0} {1} '.format(name, baseurl), nl=False
        )
        if add_oai_source(
            name=name,
            baseurl=baseurl,
            metadataprefix=metadataprefix,
            setspecs=setspecs,
            comment=comment
        ):
            click.secho('Ok', fg='green')
        else:
            click.secho('Exist', fg='red')


@oaiharvester.command('schedules')
@with_appcontext
def schedules():
    """List harvesting schedules."""
    celery_ext = current_app.extensions.get('invenio-celery')
    for key, value in celery_ext.celery.conf.beat_schedule.items():
        click.echo(key + '\t', nl=False)
        click.echo(value)


@oaiharvester.command('info')
@with_appcontext
def oaiharvester_info():
    """List infos for tasks."""
    oais = OAIHarvestConfig.query.all()
    for oai in oais:
        click.echo(oai.name)
        click.echo('\tlastrun       : {lastrun}'.format(lastrun=oai.lastrun))
        click.echo('\tbaseurl       : {baseurl}'.format(baseurl=oai.baseurl))
        click.echo('\tmetadataprefix: {pre}'.format(pre=oai.metadataprefix))
        click.echo('\tcomment       : {comment}'.format(comment=oai.comment))
        click.echo('\tsetspecs      : {sets}'.format(sets=oai.setspecs))


@oaiharvester.command('get_last_run')
@click.option('-a', '--agency', 'agency', default='',
              help="Name of persistent configuration to use.")
@with_appcontext
def get_last_run(agency):
    """Gets the lastrun for a OAI harvest configuration."""
    return oai_get_last_run(name=agency, verbose=True)


@oaiharvester.command('set_last_run')
@click.option('-n', '--name', default='',
              help="Name of persistent configuration to use.")
@click.option('-d', '--date', default=None,
              help="Last date to set for the harvesting.")
@with_appcontext
def set_last_run(name, date):
    """Sets the lastrun for a OAI harvest configuration."""
    return oai_set_last_run(name=name, date=date, verbose=True)


@oaiharvester.command()
@click.option('-n', '--name', default=None,
              help="Name of persistent configuration to use.")
@click.option('-f', '--from-date', default=None,
              help="The lower bound date for the harvesting (optional).")
@click.option('-t', '--until_date', default=None,
              help="The upper bound date for the harvesting (optional).")
@click.option('-a', '--arguments', default=[], multiple=True,
              help="Arguments to harvesting task, in the form `-a arg1=val1`.")
@click.option('-q', '--quiet', is_flag=True, default=False,
              help="Surpress output.")
@click.option('-k', '--enqueue', is_flag=True, default=False,
              help="Enqueue harvesting and return immediately.")
@click.option('-5', '--md5', 'test_md5', is_flag=True, default=False,
              help='Compaire md5 to find out if we have to update')
@click.option('-d', '--debug', 'debug', is_flag=True, default=False)
@with_appcontext
def harvestname(name, from_date, until_date, arguments, quiet, enqueue,
                test_md5, debug):
    """Harvest records from an OAI repository.

    :param name: Name of persistent configuration to use.
    :param from-date: The lower bound date for the harvesting (optional).
    :param until_date: The upper bound date for the harvesting (optional).
    :param arguments: Arguments to harvesting task, in the form
                       `-a arg1=val1`.
    :param quiet: Surpress output.
    :param enqueue: Enqueue harvesting and return immediately.
    :param test_md5: Compaire md5 to find out if we have to update.
    """
    click.secho('Harvest {name} ...'.format(name=name), fg='green')
    arguments = dict(x.split('=', 1) for x in arguments)
    harvest_task = obj_or_import_string(
        'rero_mef.authorities.{name}.tasks:process_records_from_dates'.format(
            name=name
        )
    )
    count = 0
    action_count = {}
    mef_action_count = {}
    if harvest_task:
        if enqueue:
            job = harvest_task.delay(
                from_date=from_date,
                until_date=until_date,
                test_md5=test_md5,
                verbose=(not quiet),
                debug=debug,
                **arguments
            )
            click.echo("Scheduled job {id}".format(id=job.id))
        else:
            count, action_count, mef_action_count = harvest_task(
                from_date=from_date,
                until_date=until_date,
                test_md5=test_md5,
                verbose=(not quiet),
                debug=debug,
                **arguments
            )
            click.echo(('Count: {count}'
                        ' agency: {a_counts} mef: {m_counts}').format(
                count=count,
                a_counts=action_count,
                m_counts=mef_action_count
            ))


@utils.command('export')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-p', '--pid_type', 'pid_type', default='doc')
@click.option('-o', '--outfile', 'outfile', required=True,
              type=click.File('w'))
@click.option('-i', '--pidfile', 'pidfile', type=click.File('r'),
              default=None)
@click.option('-I', '--indent', 'indent', type=click.INT, default=2)
@click.option('-s', '--schema', 'schema', is_flag=True, default=False)
@with_appcontext
def export(verbose, pid_type, outfile, pidfile, indent, schema):
    """Export record into JSON format.

    :param verbose: verbose
    :param pid_type: record type
    :param outfile: Json output file
    :param pidfile: files with pids to extract
    :param indent: indent for output
    :param schema: do not delete $schema
    """
    click.secho(
        'Export {pid_type} records: {file_name}'.format(
            pid_type=pid_type,
            file_name=outfile.name
        ),
        fg='green'
    )

    record_class = obj_or_import_string(
        current_app.config
        .get('RECORDS_REST_ENDPOINTS')
        .get(pid_type).get('record_class', Record))

    if pidfile:
        pids = pidfile
    else:
        pids = record_class.get_all_pids()

    count = 0
    output = '['
    offset = '{character:{indent}}'.format(character=' ', indent=indent)
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
                del rec['$schema']
                persons_sources = current_app.config.get(
                    'RERO_ILS_PERSONS_SOURCES', [])
                for persons_source in persons_sources:
                    try:
                        del rec[persons_sources]['$schema']
                    except:
                        pass
            output = ''
            lines = json.dumps(rec, indent=indent).split('\n')
            for line in lines:
                output += '\n{offset}{line}'.format(offset=offset, line=line)
        except Exception as err:
            click.echo(err)
            click.echo('ERROR: Can not export pid:{pid}'.format(pid=pid))
    outfile.write(output)
    outfile.write('\n]\n')


@utils.command('runindex')
@click.option('--delayed', '-d', is_flag=True,
              help='Run indexing in background.')
@click.option('--concurrency', '-c', default=1, type=int,
              help='Number of concurrent indexing tasks to start.')
@click.option('--queue', '-q', type=str,
              help='Name of the celery queue used to put the tasks into.')
@click.option('--version-type', help='Elasticsearch version type to use.')
@click.option('--raise-on-error/--skip-errors', default=True,
              help=('Controls if Elasticsearch bulk indexing'
                    ' errors raises an exception.'))
@with_appcontext
def run(delayed, concurrency, version_type=None, queue=None,
        raise_on_error=True):
    """Run bulk record indexing.

    :param delayed: Run indexing in background.
    :param concurrency: Number of concurrent indexing tasks to start.
    :param queue: Name of the celery queue used to put the tasks into.
    :param version-type: Elasticsearch version type to use.
    :param raise-on-error: 'Controls if Elasticsearch bulk indexing.
    """
    if delayed:
        celery_kwargs = {
            'kwargs': {
                'version_type': version_type,
                'es_bulk_kwargs': {'raise_on_error': raise_on_error},
            }
        }
        click.secho(
            'Starting {0} tasks for indexing records...'.format(concurrency),
            fg='green')
        if queue is not None:
            celery_kwargs.update({'queue': queue})
        for c in range(0, concurrency):
            process_bulk_queue.apply_async(**celery_kwargs)
    else:
        click.secho('Indexing records...', fg='green')
        AuthRecordIndexer(version_type=version_type).process_bulk_queue(
            es_bulk_kwargs={'raise_on_error': raise_on_error})


@utils.command('reindex')
@click.option('--yes-i-know', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Do you really want to reindex all records?')
@click.option('-t', '--pid-type', multiple=True, required=True)
@click.option('-n', '--no-info', 'no_info', is_flag=True, default=True)
@with_appcontext
def reindex(pid_type, no_info):
    """Reindex all records.

    :param pid_type: Pid type Could be multiples pid types.
    :param no-info: No `runindex` information displayed after execution.
    """
    for type in pid_type:
        click.secho(
            'Sending {type} to indexing queue ...'.format(type=type),
            fg='green'
        )

        query = (x[0] for x in PersistentIdentifier.query.filter_by(
            object_type='rec', status=PIDStatus.REGISTERED
        ).filter(
            PersistentIdentifier.pid_type == type
        ).values(
            PersistentIdentifier.object_uuid
        ))
        AuthRecordIndexer().bulk_index(query, doc_type=type)
    if no_info:
        click.secho(
            'Execute "runindex" command to process the queue!',
            fg='yellow'
        )


def queue_count():
    """Count tasks in celery."""
    inspector = inspect()
    task_count = 0
    reserved = inspector.reserved()
    if reserved:
        for key, values in reserved.items():
            task_count += len(values)
    active = inspector.active()
    if active:
        for key, values in active.items():
            task_count += len(values)
    return task_count


def wait_empty_tasks(delay, verbose=False):
    """Wait for tasks to be empty."""
    if verbose:
        spinner = itertools.cycle(['-', '\\', '|', '/'])
        click.echo(
            'Waiting: {spinner}\r'.format(spinner=next(spinner)),
            nl=False
        )
    count = queue_count()
    sleep(5)
    count += queue_count()
    while count:
        if verbose:
            click.echo(
                'Waiting: {spinner}\r'.format(spinner=next(spinner)),
                nl=False
            )
        sleep(delay)
        count = queue_count()
        sleep(5)
        count += queue_count()


@celery.command('count')
@with_appcontext
def celery_task_count():
    """Count entries in celery tasks."""
    click.secho(
        'Celery tasks active: {count}'.format(count=queue_count()),
        fg='green'
    )


@celery.command('wait_empty_tasks')
@click.option('-d', '--delay', 'delay', default=3)
@with_appcontext
def wait_empty_tasks_cli(delay):
    """Wait for tasks to be empty."""
    wait_empty_tasks(delay=delay, verbose=True)
    click.secho('No active celery tasks.', fg='green')


@utils.command('create_mef_and_agencies_from_viaf')
@click.option('-5', '--md5', 'test_md5', is_flag=True, default=False,
              help='Compaire md5 to find out if we have to update')
@click.option('-k', '--enqueue', 'enqueue', is_flag=True, default=False,
              help="Enqueue record creation.")
@click.option('-o', '--online', 'online', is_flag=True, default=False)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-w', '--wait', 'wait', is_flag=True, default=False)
@with_appcontext
def create_mef_and_agencies_from_viaf(test_md5, enqueue, online, verbose,
                                      wait):
    """Create Mef and agencies from viaf."""
    click.secho(
        'Create MEF and Agency from VIAF.',
        fg='green'
    )
    counts = {}
    agency_classes = get_agency_classes(without_mef_viaf=False)
    for name, agency_class in agency_classes.items():
        counts[name] = {}
        counts[name]['old'] = agency_class.count()
    progress = progressbar(
        items=ViafRecord.get_all_pids(),
        length=counts['viaf']['old'],
        verbose=verbose
    )
    for pid in progress:
        if enqueue:
            task = task_mef_and_agencies_from_viaf.delay(
                pid=pid,
                dbcommit=True,
                reindex=True,
                test_md5=test_md5,
                online=online,
                verbose=verbose
            )
            click.echo('viaf pid: {pid} task:{task}'.format(
                pid=pid,
                task=task
            ))
        else:
            task_mef_and_agencies_from_viaf(
                pid=pid,
                dbcommit=True,
                reindex=True,
                test_md5=test_md5,
                online=online,
                verbose=verbose
            )
    if wait:
        wait_empty_tasks(delay=3, verbose=True)
        for name, agency_class in get_agency_classes(
            without_mef_viaf=False
        ).items():
            counts[name]['new'] = agency_class.count()
        msgs = []
        counts.pop('viaf', None)
        msgs.append('mef: {old}|{new}'.format(
            old=counts['mef']['old'],
            new=counts['mef']['new']
        ))
        counts.pop('mef', None)
        for agency in counts:
            msgs.append('{agency}: {old}|{new}'.format(
                agency=agency,
                old=counts[agency]['old'],
                new=counts[agency]['new']
            ))
        click.secho('COUNTS: {counts}'.format(
            counts=', '.join(msgs)
        ), fg='blue')


@utils.command('create_mef_from_agency')
@click.option('-t', '--pid-type', 'pid_type', multiple=True,
              default=['idref', 'gnd', 'bnf', 'rero'])
@click.option('-k', '--enqueue', 'enqueue', is_flag=True, default=False,
              help="Enqueue record creation.")
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-w', '--wait', 'wait', is_flag=True, default=False)
@with_appcontext
def create_mef_from_agency(pid_type, enqueue, verbose, wait):
    """Create Mef and agencies from viaf."""
    for agency in pid_type:
        click.secho(
            'Create MEF from {agency}.'.format(agency=agency),
            fg='green'
        )
        agency_class = get_agency_class(agency)
        counts = {}
        counts[agency] = agency_class.count()
        counts['mef'] = MefRecord.count()
        for pid in progressbar(
            items=agency_class.get_all_pids(),
            length=counts[agency],
            verbose=verbose
        ):
            if enqueue:
                task = task_mef_from_agency.delay(
                    pid=pid,
                    agency=agency,
                    dbcommit=True,
                    reindex=True,
                    verbose=verbose
                )
                click.echo('{agency} pid: {pid} task:{task}'.format(
                    agency=agency,
                    pid=pid,
                    task=task
                ))
            else:
                task_mef_from_agency(
                    pid=pid,
                    agency=agency,
                    dbcommit=True,
                    reindex=True,
                    verbose=verbose
                )
        if wait:
            wait_empty_tasks(delay=3, verbose=True)
            click.secho(
                'COUNTS: mef: {m_old}|{m_new}, {agency}: {old}|{new}'.format(
                    m_old=counts['mef'],
                    m_new=MefRecord.count(),
                    agency=agency,
                    old=counts[agency],
                    new=agency_class.count(),
                ),
                fg='blue'
            )


@utils.command('flush_cache')
@click.option('--yes-i-know', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Do you really want to flush the redis cache?')
@with_appcontext
def flush_cache():
    """Flush the redis cache."""
    red = redis.StrictRedis.from_url(current_app.config['CACHE_REDIS_URL'])
    red.flushall()
    click.secho('Redis cache cleared!', fg='red')


@utils.command('agency_counts')
@with_appcontext
def agency_counts():
    """Display agency DB and ES counts."""
    def display_counts(agency, db_count, es_count):
        """Display DB, Es and SB - ES counts."""
        click.echo(
            '{agency:<5} count DB: {db_count:>10}'
            '  ES: {es_count:>10}  DB-ES: {db_es_count:>10}'.format(
                agency=agency,
                db_count=db_count,
                es_count=es_count,
                db_es_count=db_count-es_count
            )
        )
    click.secho('Display agency counts:', fg='green')
    agencies_count = {}
    for name, agency_class in get_agency_classes().items():
        search_class = get_agency_search_class(name)
        db_count = agency_class.count()
        agencies_count[name] = db_count
        display_counts(
            agency=name.upper(),
            db_count=db_count,
            es_count=search_class().filter('match_all').source('pid').count()
        )
    display_counts(
        agency='VIAF',
        db_count=ViafRecord.count(),
        es_count=ViafSearch().filter('match_all').source('pid').count()
    )
    for key in get_agencies_endpoints():
        field = '{agency}_pid'.format(agency=key)
        count = ViafSearch().filter('exists', field=field).count()
        field = '{name}_pid'.format(name=key)
        click.echo('         {name:<5}: {count:>10}'.format(
            name=key.upper(),
            count=count
        ))
    from .authorities.mef.api import MefRecord, MefSearch
    display_counts(
        agency='MEF',
        db_count=MefRecord.count(),
        es_count=MefSearch().filter('match_all').source('pid').count()
    )
    agencies = get_agencies_endpoints()
    for key, value in agencies.items():
        count = MefSearch().filter('exists', field=key).count()
        click.echo(
            '         {name:<5}: {count:>10} -DB: {diff:>10}'.format(
                name=key.upper(),
                count=count,
                diff=count-agencies_count[key]
            )
        )
