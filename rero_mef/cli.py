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
import os
import sys

import click
import yaml
from flask import current_app
from flask.cli import with_appcontext
from invenio_oaiharvester.cli import oaiharvester
from invenio_oaiharvester.models import OAIHarvestConfig
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.api import Record
from invenio_records_rest.utils import obj_or_import_string

from rero_mef.tasks import process_bulk_queue

from .authorities.api import AuthRecordIndexer
from .authorities.marctojson.records import RecordsCount
from .authorities.mef.models import MefIdentifier
from .authorities.models import AgencyAction
from .authorities.utils import add_md5, append_fixtures_new_identifiers, \
    bulk_load_agency_ids, bulk_load_agency_metadata, bulk_load_agency_pids, \
    bulk_save_agency_ids, bulk_save_agency_metadata, bulk_save_agency_pids, \
    create_agency_csv_file, create_viaf_mef_files, get_agency_class, \
    get_agency_classes
from .utils import add_oai_source


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


@fixtures.command('create_or_update')
@click.argument('agency')
@click.argument('source', type=click.File('r'), default=sys.stdin)
@click.option('-5', '--md5', 'test_md5', is_flag=True, default=False,
              help='Compaire md5 to find out if we have to update')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def create_or_update(agency, source, test_md5, verbose):
    """Create or update authority person records.

    :param agency: Agency to create or update.
    :param source: File with agencies data in json format.
    :param test_md5: Compaire md5 to find out if we have to update.
    :param verbose: Verbose.
    """
    agency_message = 'Update authority person records: {agency}'.format(
        agency=agency
    )
    click.secho(agency_message, fg='green')
    data = json.load(source)

    if isinstance(data, dict):
        data = [data]

    agency_class = get_agency_class(agency)
    for record in data:
        returned_record, action, mef_action = agency_class.create_or_update(
            record, agency=agency, dbcommit=True, reindex=True,
            test_md5=test_md5
        )
        if action != AgencyAction.DISCARD:
            id_type = ' uuid: '
            id = returned_record.id
        else:
            id_type = ' pid : '
            id = returned_record.get('pid')

        message = '{agency}{type}{id:<38} | {action}\t| {mef_action}'.format(
            agency=agency,
            type=id_type,
            id=str(id),
            action=action,
            mef_action=mef_action
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
        not_first_line = False
        pids = {}
        for record, count in records:
            if (
                (agency == 'bnf' and not record.get_fields('200')) or
                (agency == 'gnd' and not record.get_fields('100')) or
                (agency == 'rero' and not record.get_fields('100'))
            ):
                pass
            else:
                data = transformation[agency](marc=record)
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
        json_file.write('\n]\n')


def agency_membership(params):
    """Check if agency is previously configured."""
    agency = params['agency']
    params['agency_is_source'] = False
    params['agency_is_member'] = False
    with current_app.app_context():
        all_agencies = get_agency_classes()
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
@click.argument('input_directory')
@click.argument('output_directory')
@click.option('-m', '--marc_file', 'marc_file',
              help='MARC file to transform to JSON .')
@click.option('-j', '--json_file', 'json_file', help='JSON: output file.')
@click.option('-s', '--csv_pidstore_file', 'csv_pidstore_file',
              help='pidstore: CSV output file.')
@click.option('-d', '--csv_metadata_file', 'csv_metadata_file',
              help='metadata: CSV output file.')
@click.option('-p', '--rero_pids', 'rero_pids',
              help='rero pids: tab delemited file of rero ids.')
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
    :param rero_pids: rero pids: tab delemited file of rero ids.
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
                                  verbose=verbose, reindex=reindex)
        if agency == 'mef':
            ids_file_name = '{dir}/{agency}_id.csv'.format(
                dir=input_directory, agency=agency)

            message = '  Number of records in id to load: {number}. '.format(
                number=number_records_in_file(ids_file_name, 'csv'))
            click.secho(message, fg='green', err=True)

            bulk_load_agency_ids(agency, ids_file_name,  bulk_count=bulk_count,
                                 verbose=verbose)
            append_fixtures_new_identifiers(MefIdentifier, [], 'mef')


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
def info():
    """List infos for tasks."""
    oais = OAIHarvestConfig.query.all()
    for oai in oais:
        click.echo(oai.name)
        click.echo('\tlastrun       : ', nl=False)
        click.echo(oai.lastrun)
        click.echo('\tbaseurl       : ' + oai.baseurl)
        click.echo('\tmetadataprefix: ' + oai.metadataprefix)
        click.echo('\tcomment       : ' + oai.comment)
        click.echo('\tsetspecs      : ' + oai.setspecs)


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
@with_appcontext
def harvestname(name, from_date, until_date, arguments, quiet, enqueue,
                test_md5):
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
        current_app.config
        .get('RECORDS_TASKS')
        .get(name).get('harvest_task', Record)
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
                **arguments
            )
            click.echo("Scheduled job {id}".format(id=job.id))
        else:
            count, action_count, mef_action_count = harvest_task(
                from_date=from_date,
                until_date=until_date,
                test_md5=test_md5,
                verbose=(not quiet),
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
