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

import os

import click
from flask.cli import with_appcontext

from .mef.api import AgentMefRecord
from .tasks import task_create_mef_and_agents_from_viaf
from .utils import create_mef_files, create_viaf_files
from .viaf.api import AgentViafRecord
from ..utils import get_entity_classes, number_records_in_file, progressbar, \
    read_json_record


@click.group()
def agents():
    """Agent management commands."""


@agents.command()
@click.option('-k', '--enqueue', 'enqueue', is_flag=True, default=False,
              help="Enqueue record creation.")
@click.option('-o', '--online', 'online', multiple=True, default=[])
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-V', '--online_verbose', 'online_verbose', is_flag=True,
              default=False)
@click.option('-p', '--progress', 'progress', is_flag=True, default=False)
@click.option('-w', '--wait', 'wait', is_flag=True, default=False)
@click.option('-m', '--missing', 'missing', is_flag=True, default=False)
@click.option('-f', '--viaf_file', 'viaf_file', type=click.File('r'),
              default=None)
@with_appcontext
def create_from_viaf(enqueue, online, verbose, online_verbose,
                     progress, wait, missing, viaf_file):
    """Create MEF and agents from viaf."""
    def get_pids_from_json(json_file):
        """Get all pids from JSON file."""
        for record in read_json_record(viaf_file):
            yield record['pid']

    click.secho(
        'Create MEF and Agency from VIAF.',
        fg='green'
    )
    non_existing_pids = {}
    agent_classes = get_entity_classes(without_mef_viaf=False)
    counts = {name: {'old': agent_class.count()}
              for name, agent_class in agent_classes.items()}

    if missing:
        missing_pids, non_existing_pids = AgentMefRecord. \
            get_all_missing_viaf_pids(
                verbose=progress or verbose
            )
        progress_bar = progressbar(
            items=missing_pids,
            length=len(missing_pids),
            verbose=progress
        )
    elif viaf_file:
        progress_bar = progressbar(
            items=get_pids_from_json(viaf_file),
            length=number_records_in_file(viaf_file.name, 'json'),
            verbose=progress
        )
    else:
        progress_bar = progressbar(
            items=AgentViafRecord.get_all_pids(),
            length=counts['viaf']['old'],
            verbose=progress
        )
    for pid in progress_bar:
        if enqueue:
            task = task_create_mef_and_agents_from_viaf.delay(
                pid=pid,
                dbcommit=True,
                reindex=True,
                online=online
            )
            click.echo(f'viaf pid: {pid} task:{task}')
        else:
            task_create_mef_and_agents_from_viaf(
                pid=pid,
                dbcommit=True,
                reindex=True,
                online=online,
                verbose=verbose,
                online_verbose=online_verbose
            )

    if non_existing_pids:
        click.echo(
            f'Clean VIAF pids from MEF records: {len(non_existing_pids)}')
        for pid, viaf_pid in non_existing_pids.items():
            # TODO: clean MEF records with non existing VIAF pids:
            pass

    if wait:
        from ..cli import wait_empty_tasks
        wait_empty_tasks(delay=3, verbose=True)
        for name, agent_class in get_entity_classes(
            without_mef_viaf=False
        ).items():
            counts[name]['new'] = agent_class.count()
        counts.pop('viaf', None)
        msgs = [f'mef: {counts["mef"]["old"]}|{counts["mef"]["new"]}']
        counts.pop('mef', None)
        msgs.extend(f"{agent}: {value['old']}|{counts[agent]['new']}"
                    for agent, value in counts.items())

        click.secho(
            f'COUNTS: {", ".join(msgs)}',
            fg='blue'
        )


@agents.command()
@click.argument('viaf_file')
@click.argument('output_directory')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def create_csv_viaf(viaf_file, output_directory, verbose):
    """Create VIAF CSV from VIAF source text file.

    :param viaf_file: VIAF source text file.
    :param output_directory: Output directory.
    :param verbose: Verbose.
    """
    click.secho('  Create VIAF CSV files.', err=True)
    pidstore = os.path.join(output_directory, 'viaf_pidstore.csv')
    metadata = os.path.join(output_directory, 'viaf_metadata.csv')
    click.secho(
        f'  VIAF input file: {viaf_file}',
        err=True)

    count = create_viaf_files(
        viaf_input_file_name=viaf_file,
        viaf_pidstore_file_name=pidstore,
        viaf_metadata_file_name=metadata,
        verbose=verbose
    )
    click.secho(
        f'  Number of VIAF records created: {count}.',
        fg='green',
        err=True)


@agents.command()
@click.argument('viaf_metadata_file')
@click.argument('output_directory')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def create_csv_mef(viaf_metadata_file, output_directory, verbose):
    """Create MEF CSV from INVENIO metadata file.

    :param viaf_metadata_file: VIAF metadata CSV file.
    :param output_directory: Output directory.
    :param verbose: Verbose.
    """
    click.secho('  Create MEF CSV files from VIAF metadata.', err=True)
    pidstore = os.path.join(output_directory, 'mef_pidstore.csv')
    metadata = os.path.join(output_directory, 'mef_metadata.csv')
    ids = os.path.join(output_directory, 'mef_id.csv')

    click.secho(
        f'  VIAF input file: {viaf_metadata_file}',
        err=True)
    message = f'  CSV output files: {pidstore}, {metadata}'

    count = create_mef_files(
            viaf_metadata_file_name=viaf_metadata_file,
            input_directory=output_directory,
            mef_pidstore_file_name=pidstore,
            mef_metadata_file_name=metadata,
            mef_ids_file_name=ids,
            verbose=verbose
        )

    click.secho(
        f'  Number of MEF records created: {count}.',
        fg='green',
        err=True)
