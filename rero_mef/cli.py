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
"""Click command-line interface for MEF record management."""

from __future__ import absolute_import, print_function

import copy
import json
import os
import sys

import click
import redis
import yaml
from flask import current_app
from flask.cli import with_appcontext
from flask_security.confirmable import confirm_user
from invenio_accounts.cli import commit, users
from invenio_oaiharvester.cli import oaiharvester
from invenio_oaiharvester.models import OAIHarvestConfig
from invenio_records_rest.utils import obj_or_import_string
from sqlitedict import SqliteDict
from werkzeug.local import LocalProxy

from .agents.cli import create_mef_and_agents_from_viaf, \
    create_mef_from_agent, queue_count, reindex_missing, wait_empty_tasks
from .marctojson.helper import nice_record
from .marctojson.records import RecordsCount
from .mef.models import MefIdentifier
from .tasks import create_or_update as task_create_or_update
from .tasks import delete as task_delete
from .tasks import process_bulk_queue as task_process_bulk_queue
from .utils import add_md5, add_oai_source, append_fixtures_new_identifiers, \
    bulk_load_agent_ids, bulk_load_agent_metadata, bulk_load_agent_pids, \
    bulk_save_agent_ids, bulk_save_agent_metadata, bulk_save_agent_pids, \
    create_agent_csv_file, create_mef_files, create_viaf_files, \
    export_json_records, get_agent_class, get_agent_classes, \
    get_agent_indexer_class, get_agent_search_class, number_records_in_file, \
    oai_get_last_run, oai_set_last_run, read_json_record
from .viaf.api import ViafRecord, ViafSearch

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


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


utils.add_command(create_mef_and_agents_from_viaf)
utils.add_command(create_mef_from_agent)
utils.add_command(reindex_missing)


@click.group()
def celery():
    """Celery management commands."""


@fixtures.command('create_or_update')
@click.argument('agent')
@click.argument('source', type=click.File('r'), default=sys.stdin)
@click.option('-l', '--lazy', 'lazy', is_flag=True, default=False)
@click.option('-5', '--md5', 'test_md5', is_flag=True, default=False,
              help='Compaire md5 to find out if we have to update')
@click.option('-k', '--enqueue', 'enqueue', is_flag=True, default=False,
              help="Enqueue record creation.")
@click.option('-o', '--online', 'online', is_flag=True, default=False)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def create_or_update(agent, source, lazy, test_md5, enqueue, online, verbose):
    """Create or update authority person records.

    :param agent: Agency to create or update.
    :param source: File with agents data in json format.
    :param lazy: lazy reads file
    :param test_md5: Compaire md5 to find out if we have to update.
    :param online: Try to get viaf online if not exist.
    :param verbose: Verbose.
    """
    agent_message = 'Update records: {agent}'.format(
        agent=agent
    )
    click.secho(agent_message, fg='green')
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
                agent=agent,
                dbcommit=True,
                reindex=True,
                test_md5=test_md5,
                online=online,
                verbose=verbose
            )
        else:
            task_create_or_update(
                index=count,
                record=record,
                agent=agent,
                dbcommit=True,
                reindex=True,
                test_md5=test_md5,
                online=online,
                verbose=verbose
            )


@fixtures.command('delete')
@click.argument('agent')
@click.argument('source', type=click.File('r'), default=sys.stdin)
@click.option('-l', '--lazy', 'lazy', is_flag=True, default=False)
@click.option('-k', '--enqueue', 'enqueue', is_flag=True, default=False,
              help="Enqueue record deletion.")
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def delete(agent, source, lazy, enqueue, verbose):
    """Delete authority person records.

    :param agent: Agency to create or update.
    :param source: File with agents data in json format.
    :param lazy: lazy reads file
    :param verbose: Verbose.
    """
    agent_message = 'Delete authority person records: {agent}'.format(
        agent=agent
    )
    click.secho(agent_message, fg='green')
    if lazy:
        # try to lazy read json file (slower, better memory management)
        data = read_json_record(source)
    else:
        data = json.load(source)
        if isinstance(data, dict):
            data = [data]

    for count, record in enumerate(data):
        if enqueue:
            task_delete.delay(
                index=count,
                pid=record.get('pid'),
                agent=agent,
                dbcommit=True,
                delindex=True,
                verbose=verbose
            )
        else:
            task_delete(
                index=count,
                pid=record.get('pid'),
                agent=agent,
                dbcommit=True,
                delindex=True,
                verbose=verbose
            )
    # if agent == 'viaf':
    #     if enqueue:
    #         wait_empty_tasks(delay=3, verbose=True)
    #     count = 0
    #     for pid in MefRecord.get_all_empty_pids():
    #         count += 1
    #         mef_record = MefRecord.get_record_by_pid(pid)
    #         mef_record.delete(dbcommit=True, delindex=True)
    #     click.secho(
    #         'Mef records deleted: {count}'.format(count=count),
    #         fg='yellow'
    #     )


def marc_to_json(agent, marc_file, json_file, json_deleted_file, verbose):
    """Marc to JSON conversion."""
    with current_app.app_context():
        transformation = current_app.config.get('TRANSFORMATION')
        records = []
        try:
            records = RecordsCount(str(marc_file))
        except Exception as error:
            agent_message = 'Marc file not found for {ag}:{err}'.format(
                ag=agent, err=error
            )
            click.secho(agent_message, fg='red', err=True)

        if json_file:
            json_file = open(json_file, 'w', encoding='utf8')
            json_deleted_file = open(json_deleted_file, 'w', encoding='utf8')
        else:
            json_file = sys.stdout
            json_deleted_file = sys.stderr

        json_file.write('[\n')
        json_deleted_file.write('[\n')
        not_first_line = False
        not_first_deleted = False
        pids = {}
        for record, count in records:
            data = transformation[agent](
                marc=record,
                logger=current_app.logger,
                verbose=True
            )
            if data.json:
                pid = data.json.get('pid')
                if pids.get(pid):
                    click.secho(
                        '  Error duplicate pid in {agent}: {pid}'.format(
                            agent=agent,
                            pid=pid
                        ),
                        fg='red'
                    )
                else:
                    pids[pid] = 1
                    add_md5(data.json)
                    if data.json.get('deleted'):
                        if not_first_deleted:
                            json_deleted_file.write(',\n')
                        json.dump(data.json, json_deleted_file,
                                  ensure_ascii=False, indent=2)
                        not_first_deleted = True
                    else:
                        if not_first_line:
                            json_file.write(',\n')
                        json.dump(data.json, json_file, ensure_ascii=False,
                                  indent=2)
                        not_first_line = True
            else:
                click.secho(
                    'Error transformation marc {agent}:\n{rec}'.format(
                        agent=agent,
                        rec=nice_record(record)
                    ),
                    fg='yellow'
                )
        json_file.write('\n]\n')
        json_deleted_file.write('\n]\n')


def agent_membership(params):
    """Check if agent is previously configured."""
    agent = params['agent']
    params['agent_is_source'] = False
    params['agent_is_member'] = False
    with current_app.app_context():
        all_agents = get_agent_classes(without_mef_viaf=False)
        if agent in all_agents:
            params['agent_is_member'] = True
        agents = copy.deepcopy(all_agents)
        del agents['viaf']
        del agents['mef']
        if agent in agents:
            params['agent_is_source'] = True


def marctojson_action(params):
    """Check if marc to json transformation is required."""
    params['marctojson'] = False
    if (
        params['agent_is_source'] and
        params['marc_file'] and params['json_file']
    ):
        params['marctojson'] = True


def csv_action(params):
    """Check if json to csv transformation is required."""
    params['csv_action'] = False
    if (
        params['agent_is_member'] and
        not params['agent_is_source'] and
        params['json_file'] and
        params['csv_pidstore_file'] and
        params['csv_metadata_file']
    ):
        params['csv_action'] = True
    elif (
        params['agent_is_member'] and
        params['agent_is_source'] and
        params['json_file'] and
        params['csv_pidstore_file'] and
        params['csv_metadata_file']
    ):
        params['csv_action'] = True


def db_action(params):
    """Check if db load is required."""
    params['db_action'] = False
    if (
        params['agent_is_member'] and
        params['csv_pidstore_file'] and
        params['csv_metadata_file'] and
        params['load_records']
    ):
        params['db_action'] = True


def valid_agent(params):
    """Check agent is valid."""
    if 'agent' in params:
        params['valid'] = True
    else:
        params['valid'] = False


@fixtures.command('bulk_load')
@click.argument('agent')
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
@click.option('-c', '--bulk_count', 'bulkcount', default=0, type=int,
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
    valid_agent(params)
    agent_membership(params)
    marctojson_action(params)
    csv_action(params)
    db_action(params)
    agent = params['agent']
    verbose = params['verbose']
    reindex = params['reindex']
    if params['bulkcount'] > 0:
        bulk_count = params['bulkcount']
    else:
        bulk_count = current_app.config.get('BULK_CHUNK_COUNT', 100000)

    input_directory = params['input_directory']
    output_directory = params['output_directory']

    message = ' Tasks for agent: {agent}'.format(agent=agent)
    click.secho(message, err=True)

    if 'marctojson' in params and params['marctojson']:
        marc_file = '{dir}/{file}'.format(
            dir=input_directory, file=params['marc_file'])
        json_file = '{dir}/{file}'.format(
            dir=output_directory, file=params['json_file'])
        json_deleted_file = '{file_name}_deleted{ext}'.format(
            file_name=os.path.splitext(json_file)[0],
            ext=os.path.splitext(json_file)[-1]
        )
        message = \
            ' Transform {agent} MARC to JSON. {file} {deleted_file}'.format(
                agent=agent,
                file=json_file,
                deleted_file=json_deleted_file
            )
        click.secho(message, err=True)
        marc_to_json(
            agent=agent,
            marc_file=marc_file,
            json_file=json_file,
            json_deleted_file=json_deleted_file,
            verbose=verbose
        )

        message = '  Number of {agent} JSON records created: {nbr}.'.format(
            agent=agent,
            nbr=number_records_in_file(json_file, 'json')
        )
        click.secho(message, fg='green', err=True)
        message = '  Number of {agent} JSON records deleted: {nbr}. '.format(
            agent=agent,
            nbr=number_records_in_file(json_deleted_file, 'json')
        )
        click.secho(message, fg='green', err=True)

    if 'csv_action' in params and params['csv_action']:
        message = '  Create {agent} CSV files from JSON. '.format(
            agent=agent
        )
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
        if agent == 'mef':
            ids = os.path.join(output_directory, 'mef_id.csv')
            message += ', {ids}'.format(ids=ids)
        click.secho(message, err=True)

        if params['agent_is_source']:
            create_agent_csv_file(json_file, agent, pidstore, metadata)
        else:
            if agent == 'viaf':
                create_viaf_files(
                    viaf_input_file=json_file,
                    viaf_pidstore_file_name=pidstore,
                    viaf_metadata_file_name=metadata,
                    verbose=verbose
                )
            elif agent == 'mef':
                create_mef_files(
                    viaf_pidstore_file=json_file,
                    input_directory=input_directory,
                    mef_pidstore_file_name=pidstore,
                    mef_metadata_file_name=metadata,
                    mef_ids_file_name=ids,
                    verbose=verbose
                )
        message = \
            '  Number of {agent} records created in pidstore: {nbr}. '.format(
                agent=agent,
                nbr=number_records_in_file(pidstore, 'csv')
            )
        click.secho(message, fg='green', err=True)
        message = \
            '  Number of {agent} records created in metadata: {nbr}. '.format(
                agent=agent,
                nbr=number_records_in_file(metadata, 'csv')
            )
        click.secho(message, fg='green', err=True)
        if agent == 'mef':
            message = \
                '  Number of {agent} records created in ids: {nbr}. '.format(
                    agent=agent,
                    nbr=number_records_in_file(ids, 'csv')
                )
            click.secho(message, fg='green', err=True)

    if 'db_action' in params and params['db_action']:
        message = '  Load {agent} CSV files into database. '.format(
            agent=agent
        )
        click.secho(message, err=True)
        pidstore = os.path.join(input_directory, params['csv_pidstore_file'])
        metadata = os.path.join(input_directory, params['csv_metadata_file'])
        message = '  CSV input files: {pidstore}|{metadata} '.format(
            pidstore=pidstore, metadata=metadata)
        click.secho(message, err=True)

        message = '  Number of records in pidstore to load: {number}. '.format(
            number=number_records_in_file(pidstore, 'csv'))
        click.secho(message, fg='green', err=True)

        bulk_load_agent_pids(agent, pidstore, bulk_count=bulk_count,
                             verbose=verbose)

        message = '  Number of records in metadata to load: {number}. '.format(
            number=number_records_in_file(metadata, 'csv'))
        click.secho(message, fg='green', err=True)

        bulk_load_agent_metadata(agent, metadata, bulk_count=bulk_count,
                                 verbose=verbose, reindex=reindex)
        if agent == 'mef':
            ids_file_name = os.path.join(
                input_directory,
                '{agent}_id.csv'.format(agent=agent)
            )
            if os.path.exists(ids_file_name):
                message = '  {msg}: {number}. '.format(
                    msg='Number of records in id to load: {number}',
                    number=number_records_in_file(ids_file_name, 'csv'))
                click.secho(message, fg='green', err=True)

                bulk_load_agent_ids(agent, ids_file_name,
                                    bulk_count=bulk_count, verbose=verbose)
                append_fixtures_new_identifiers(MefIdentifier, [], 'mef')
        # set last run if file exist
        file_name = os.path.join(
            output_directory,
            '{agent}_last_run.txt'.format(agent=agent)
        )
        try:
            with open(file_name) as last_run_file:
                last_run = last_run_file.readline()
                if verbose:
                    click.secho(
                        '  Set last run: {lastrun}'.format(lastrun=last_run),
                        fg='green'
                    )
                oai_set_last_run(agent, last_run)
        except Exception:
            pass


@fixtures.command('bulk_save')
@click.argument('output_directory')
@click.option('-a', '--agents', 'agents', multiple=True,
              default=['aggnd', 'aidref', 'agrero', 'corero', 'mef', 'viaf'])
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def bulk_save(agents, output_directory, verbose):
    """Agencies record dump.

    :param agents: Agencies to export.
        default=['aggnd', 'aidref', 'agrero', 'corero', 'mef', 'viaf'])
    :param verbose: Verbose.
    """
    for agent in agents:
        click.secho(
            'Save {agent} CSV files to directory: {path}'.format(
                agent=agent,
                path=output_directory,
            ),
            fg='green'
        )
        file_name = os.path.join(
            output_directory,
            '{agent}_metadata.csv'.format(agent=agent)
        )
        if verbose:
            click.echo(
                '  Save metadata: {file_name}'.format(file_name=file_name))
        bulk_save_agent_metadata(agent, file_name=file_name, verbose=False)
        file_name = os.path.join(
            output_directory,
            '{agent}_pidstore.csv'.format(agent=agent)
        )
        if verbose:
            click.echo(
                '  Save pidstore: {file_name}'.format(file_name=file_name))
        bulk_save_agent_pids(agent, file_name=file_name, verbose=False)
        if agent == 'mef':
            file_name = os.path.join(
                output_directory,
                '{agent}_id.csv'.format(agent=agent)
            )
            if verbose:
                click.echo(
                    '  Save id: {file_name}'.format(file_name=file_name))
            bulk_save_agent_ids(agent, file_name=file_name, verbose=False)
        last_run = oai_get_last_run(agent)
        if last_run:
            file_name = os.path.join(
                output_directory,
                '{agent}_last_run.txt'.format(agent=agent)
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
@click.option('-s', '--sqlite_dict', 'sqlite_dict', default='sqlite_dict.db')
@with_appcontext
def csv_diff(csv_metadata_file, csv_metadata_file_compair, agent, output,
             indent, verbose, sqlite_dict):
    """Agencies record diff.

    :param csv_metadata_file: csv metadata file to compair.
    :param csv_metadata_file_compair: csv metadata file to compair too.
    :param agent: agent type to compair too.
    :param verbose: Verbose.
    :param sqlite_dict: SqliteDict Db file name.
    """
    def get_pid_data(line):
        """Get json from CSV text line.

        :param line: line of CSV text.
        :returns: data as json
        """
        data = json.loads(line.split('\t')[3].replace('\\\\', '\\'))
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

    compaire_data = SqliteDict(sqlite_dict, autocommit=True)
    if csv_metadata_file_compair and not agent:
        length = number_records_in_file(csv_metadata_file_compair, 'csv')
        with open(csv_metadata_file_compair, 'r', buffering=1) as meta_file:
            label = 'Loading: {name}'.format(name=compair)
            with click.progressbar(meta_file, length=length,
                                   label=label) as metadata:
                for metadata_line in metadata:
                    pid, data = get_pid_data(metadata_line)
                    compaire_data[pid] = data
    elif agent:
        agent_class = get_agent_class(agent)
        length = agent_class.count()
        ids = agent_class.get_all_ids()
        with click.progressbar(ids, length=length) as record_ids:
            for id in record_ids:
                record = agent_class.get_record_by_id(id)
                pid = record.pid
                compaire_data[pid] = record

    with open(csv_metadata_file, 'r', buffering=1) as metadata_file:
        for idx, metadata_line in enumerate(metadata_file):
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
                        if idx > 0:
                            file_diff.write(',')
                        file_diff.write(intent_output(data, indent))
                del(compaire_data[pid])
            else:
                click.echo('NEW :\t{data}'.format(
                    data=json.dumps(data, sort_keys=True)
                ))
                if output:
                    if idx > 0:
                        file_new.write(',')
                    file_new.write(intent_output(data, indent))
    idx = 0
    for pid, data in compaire_data.items():
        click.echo('DEL :\t{data}'.format(
            data=json.dumps(data, sort_keys=True)
        ))
        if output:
            if idx > 0:
                file_delete.write(',')
            file_delete.write(intent_output(data, indent))
            idx += 1

    if output:
        file_new.write('\n]')
        file_new.close()
        file_diff.write('\n]')
        file_diff.close()
        file_delete.write('\n]')
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
@click.option(
    '-u', '--update', is_flag=True, default=False, help='Update config'
)
@with_appcontext
def add_oai_source_config(name, baseurl, metadataprefix, setspecs, comment,
                          update):
    """Add OAIHarvestConfig.

    :param name: Name of OAI source.
    :param baseurl: Baseurl of OAI source.
    :param metadataprefix: The prefix for the metadata
    :param setspecs: The `set` criteria for the harvesting
    :param comment: Comment
    :param update: update config
    """
    click.echo('Add OAIHarvestConfig: {0} '.format(name), nl=False)
    msg = add_oai_source(
        name=name,
        baseurl=baseurl,
        metadataprefix=metadataprefix,
        setspecs=setspecs,
        comment=comment,
        update=update
    )
    click.echo(msg)


@oaiharvester.command('initconfig')
@click.argument('configfile', type=click.File('rb'))
@click.option(
    '-u', '--update', is_flag=True, default=False, help='Update config'
)
@with_appcontext
def init_oai_harvest_config(configfile, update):
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
        msg = add_oai_source(
            name=name,
            baseurl=baseurl,
            metadataprefix=metadataprefix,
            setspecs=setspecs,
            comment=comment,
            update=update
        )
        click.echo(msg)


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
@click.option('-n', '--name', 'name', default='',
              help="Name of persistent configuration to use.")
@with_appcontext
def get_last_run(name):
    """Gets the lastrun for a OAI harvest configuration."""
    return oai_get_last_run(name=name, verbose=True)


@oaiharvester.command('set_last_run')
@click.option('-n', '--name', default='',
              help="Name of persistent configuration to use.")
@click.option('-d', '--date', default=None,
              help="Last date to set for the harvesting.")
@with_appcontext
def set_last_run(name, date):
    """Sets the lastrun for a OAI harvest configuration."""
    return oai_set_last_run(name=name, date=date, verbose=True)


@oaiharvester.command('harvestname')
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
@click.option('-d', '--debug', 'debug', is_flag=True, default=False,
              help='Print debug informations')
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
        'rero_mef.agents.{nam}.tasks:process_records_from_dates'.format(
            nam=name
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
                        ' agent: {a_counts} mef: {m_counts}').format(
                count=count,
                a_counts=action_count,
                m_counts=mef_action_count
            ))


@oaiharvester.command('save')
@click.argument('output_file_name')
@click.option('-n', '--name', default=None,
              help="Name of persistent configuration to use.")
@click.option('-f', '--from-date', default=None,
              help="The lower bound date for the harvesting (optional).")
@click.option('-t', '--until_date', default=None,
              help="The upper bound date for the harvesting (optional).")
@click.option('-q', '--quiet', is_flag=True, default=False,
              help="Surpress output.")
@click.option('-k', '--enqueue', is_flag=True, default=False,
              help="Enqueue harvesting and return immediately.")
@with_appcontext
def save(output_file_name, name, from_date, until_date, quiet, enqueue):
    """Harvest records from an OAI repository and save to file.

    :param name: Name of persistent configuration to use.
    :param from-date: The lower bound date for the harvesting (optional).
    :param until_date: The upper bound date for the harvesting (optional).
    :param quiet: Surpress output.
    :param enqueue: Enqueue harvesting and return immediately.
    """
    click.secho('Harvest {name} ...'.format(name=name), fg='green')
    save_task = obj_or_import_string(
        'rero_mef.agents.{name}.tasks:save_records_from_dates'.format(
            name=name
        )
    )
    count = 0
    if save_task:
        if enqueue:
            job = save_task.delay(
                file_name=output_file_name,
                from_date=from_date,
                until_date=until_date,
                verbose=(not quiet)
            )
            click.echo("Scheduled job {id}".format(id=job.id))
        else:
            count = save_task(
                file_name=output_file_name,
                from_date=from_date,
                until_date=until_date,
                verbose=(not quiet)
            )
            click.echo('Count: {count}'.format(count=count))


@utils.command('export')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-t', '--pid_type', 'pid_type', default='doc')
@click.option('-o', '--outfile', 'outfile', required=True)
@click.option('-i', '--pidfile', 'pidfile', type=click.File('r'),
              default=None)
@click.option('-I', '--indent', 'indent', type=click.INT, default=2)
@click.option('-s', '--schema', 'schema', is_flag=True, default=False)
@with_appcontext
def export(verbose, pid_type, outfile, pidfile, indent, schema):
    """Export one record into JSON format.

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
        .get(pid_type).get('record_class')
    )
    if pidfile:
        pids = pidfile
    else:
        pids = record_class.get_all_pids()
    export_json_records(
        pids=pids,
        pid_type=pid_type,
        output_file_name=outfile,
        indent=indent,
        schema=schema,
        verbose=verbose
    )


@utils.command('export_agents')
@click.argument('output_path')
@click.option('-t', '--pid-type', 'pid_type', multiple=True,
              default=['viaf', 'mef', 'aggnd', 'aidref', 'agrero', 'corero'])
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-I', '--indent', 'indent', type=click.INT, default=2)
@click.option('-s', '--schema', 'schema', is_flag=True, default=False)
@with_appcontext
def export_agents(output_path, pid_type, verbose, indent, schema):
    """Export multiple records into JSON format.

    :param pid_type: record type
    :param verbose: verbose
    :param pidfile: files with pids to extract
    :param indent: indent for output
    :param schema: do not delete $schema
    """
    for p_type in pid_type:
        output_file_name = os.path.join(
            output_path, '{pid_type}.json'.format(pid_type=p_type))
        click.secho(
            'Export {pid_type} records: {file_name}'.format(
                pid_type=p_type,
                file_name=output_file_name
            ),
            fg='green'
        )
        record_class = obj_or_import_string(
            current_app.config
            .get('RECORDS_REST_ENDPOINTS')
            .get(p_type).get('record_class')
        )
        export_json_records(
            pids=record_class.get_all_pids(),
            pid_type=p_type,
            output_file_name=output_file_name,
            indent=indent,
            schema=schema,
            verbose=verbose
        )


@utils.command('runindex')
@click.option('--delayed', '-d', is_flag=True,
              help='Run indexing in background.')
@click.option('--concurrency', '-c', default=1, type=int,
              help='Number of concurrent indexing tasks to start.')
@click.option(
    '--with_stats', is_flag=True, default=False,
    help='report number of successful and list failed error response.')
@click.option('--queue', '-q', type=str,
              help='Name of the celery queue used to put the tasks into.')
@click.option('--version-type', help='Elasticsearch version type to use.')
@click.option('--raise-on-error/--skip-errors', default=True,
              help=('Controls if Elasticsearch bulk indexing'
                    ' errors raises an exception.'))
@with_appcontext
def run(delayed, concurrency, with_stats, version_type=None, queue=None,
        raise_on_error=True):
    """Run bulk record indexing.

    :param delayed: Run indexing in background.
    :param concurrency: Number of concurrent indexing tasks to start.
    :param queue: Name of the celery queue used to put the tasks into.
    :param version-type: Elasticsearch version type to use.
    :param raise-on-error: 'Controls if Elasticsearch bulk indexing.
    """
    celery_kwargs = {
        'kwargs': {
            'version_type': version_type,
            'es_bulk_kwargs': {'raise_on_error': raise_on_error},
            'stats_only': not with_stats
        }
    }
    if delayed:
        click.secho(
            'Starting {0} tasks for indexing records...'.format(concurrency),
            fg='green')
        if queue is not None:
            celery_kwargs.update({'queue': queue})
        for c in range(0, concurrency):
            process_id = task_process_bulk_queue.delay(
                version_type=version_type,
                es_bulk_kwargs={'raise_on_error': raise_on_error},
                stats_only=not with_stats
            )
            click.secho('index async: {process_id}'.format(
                process_id=process_id), fg='yellow')
    else:
        click.secho('Indexing records...', fg='green')
        indexed, error = task_process_bulk_queue(
            version_type=version_type,
            es_bulk_kwargs={'raise_on_error': raise_on_error},
            stats_only=not with_stats
        )
        click.secho('indexed: {indexed}, error: {error}'.format(
            indexed=indexed, error=error), fg='yellow')


@utils.command('reindex')
@click.option('--yes-i-know', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Do you really want to reindex all records?')
@click.option('-t', '--pid_type', "pid_type", multiple=True, required=True)
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
        agent_class = get_agent_class(type)
        agent_indexer = get_agent_indexer_class(type)
        agent_indexer().bulk_index(agent_class.get_all_ids())
    if no_info:
        click.secho(
            'Execute "runindex" command to process the queue!',
            fg='yellow'
        )


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


@utils.command('agent_counts')
@with_appcontext
def agent_counts():
    """Display agent DB and ES counts."""
    def display_counts(agent, db_count, es_count):
        """Display DB, Es and SB - ES counts."""
        click.echo(
            '{agent:<6} count DB: {db_count:>10}'
            '  ES: {es_count:>10}  DB-ES: {db_es_count:>10}'.format(
                agent=agent,
                db_count=db_count,
                es_count=es_count,
                db_es_count=db_count-es_count
            )
        )
    click.secho('Display agent counts:', fg='green')
    agents_count = {}
    agents_deleted = {}
    for name, agent_class in get_agent_classes().items():
        search_class = get_agent_search_class(name)
        db_count = agent_class.count()
        agents_count[name] = db_count
        display_counts(
            agent=name.upper(),
            db_count=db_count,
            es_count=search_class().filter('match_all').source('pid').count()
        )
        deleted = search_class().filter('exists', field='deleted').count()
        agents_deleted[name] = deleted

    display_counts(
        agent='VIAF',
        db_count=ViafRecord.count(),
        es_count=ViafSearch().filter('match_all').source('pid').count()
    )
    for name, agent_class in get_agent_classes().items():
        field = getattr(agent_class, 'viaf_pid_name')
        if field:
            count = ViafSearch().filter('exists', field=field).count()
            click.echo('         {name:<6}: {count:>10}'.format(
                name=name.upper(),
                count=count
            ))
    from .mef.api import MefRecord, MefSearch
    display_counts(
        agent='MEF',
        db_count=MefRecord.count(),
        es_count=MefSearch().filter('match_all').source('pid').count()
    )
    for name, agent_class in get_agent_classes().items():
        field = getattr(agent_class, 'viaf_pid_name')
        if field:
            count = MefSearch(). \
                filter('exists', field=agent_class.name).count()
            click.echo(
                '         {name:<6}: {count:>10}'
                ' -DB: {diff:>10}'
                ' deleted: {d_count}'.format(
                    name=name.upper(),
                    count=count,
                    diff=count-agents_count[name],
                    d_count=agents_deleted[name]
                )
            )


@users.command('confirm')
@click.argument('user')
@with_appcontext
@commit
def manual_confirm_user(user):
    """Confirm a user."""
    user_obj = _datastore.get_user(user)
    if user_obj is None:
        raise click.UsageError('ERROR: User not found.')
    if confirm_user(user_obj):
        click.secho('User "%s" has been confirmed.' % user, fg='green')
    else:
        click.secho('User "%s" was already confirmed.' % user, fg='yellow')
