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
from .tasks import create_from_viaf as task_mef_and_agents_from_viaf
from .tasks import create_mef as task_mef_from_agent
from .utils import create_mef_files, create_viaf_files
from .viaf.api import AgentViafRecord
from ..utils import get_entity_class, get_entity_classes, progressbar


@click.group()
def agents():
    """Agent management commands."""


@agents.command()
@click.option('-5', '--md5', 'test_md5', is_flag=True, default=False,
              help='Compaire md5 to find out if we have to update')
@click.option('-k', '--enqueue', 'enqueue', is_flag=True, default=False,
              help="Enqueue record creation.")
@click.option('-o', '--online', 'online', is_flag=True, default=False)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-p', '--progress', 'progress', is_flag=True, default=False)
@click.option('-w', '--wait', 'wait', is_flag=True, default=False)
@click.option('-m', '--missing', 'missing', is_flag=True, default=False)
@with_appcontext
def create_from_viaf(test_md5, enqueue, online, verbose, progress, wait,
                     missing):
    """Create MEF and agents from viaf."""
    click.secho(
        'Create MEF and Agency from VIAF.',
        fg='green'
    )
    counts = {}
    agent_classes = get_entity_classes(without_mef_viaf=False)
    for name, agent_class in agent_classes.items():
        counts[name] = {}
        counts[name]['old'] = agent_class.count()
    if missing:
        missing_pids = AgentMefRecord.get_all_missing_viaf_pids(
            verbose=progress or verbose
        )
        progress_bar = progressbar(
            items=missing_pids,
            length=len(missing_pids),
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
            task = task_mef_and_agents_from_viaf.delay(
                pid=pid,
                dbcommit=True,
                reindex=True,
                test_md5=test_md5,
                online=online
            )
            click.echo(f'viaf pid: {pid} task:{task}')
        else:
            task_mef_and_agents_from_viaf(
                pid=pid,
                dbcommit=True,
                reindex=True,
                test_md5=test_md5,
                online=online,
                verbose=verbose
            )
    if wait:
        from ..cli import wait_empty_tasks
        wait_empty_tasks(delay=3, verbose=True)
        for name, agent_class in get_entity_classes(
            without_mef_viaf=False
        ).items():
            counts[name]['new'] = agent_class.count()
        msgs = []
        counts.pop('viaf', None)
        msgs.append(f'mef: {counts["mef"]["old"]}|{counts["mef"]["new"]}')
        counts.pop('mef', None)
        for agent in counts:
            msgs.append(
                f'{agent}: {counts[agent]["old"]}|{counts[agent]["new"]}')
        click.secho(
            f'COUNTS: {", ".join(msgs)}',
            fg='blue'
        )


@agents.command()
@click.option('-t', '--pid_type', 'pid_type', multiple=True,
              default=['aidref', 'aggnd', 'agrero'])
@click.option('-k', '--enqueue', 'enqueue', is_flag=True, default=False,
              help="Enqueue record creation.")
@click.option('-o', '--online', 'online', is_flag=True, default=False)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-p', '--progress', 'progress', is_flag=True, default=False)
@click.option('-w', '--wait', 'wait', is_flag=True, default=False)
@click.option('-m', '--missing', 'missing', is_flag=True, default=False)
@with_appcontext
def create_mef(pid_type, enqueue, online, verbose, progress, wait, missing):
    """Create MEF from agents."""
    if missing:
        missing_pids, to_much_pids = \
            AgentMefRecord.get_all_missing_agents_pids(
                agents=pid_type,
                verbose=progress
            )
    for agent in pid_type:
        if agent not in ['aidref', 'aggnd', 'agrero']:
            click.secho(
                f'Error create MEF from {agent}. Wrong agent!',
                fg='red'
            )
        else:
            click.secho(
                f'Create MEF from {agent}.',
                fg='green'
            )
            agent_class = get_entity_class(agent)
            counts = {}
            counts[agent] = agent_class.count()
            counts['mef'] = AgentMefRecord.count()
            if missing:
                progress_bar = progressbar(
                    items=missing_pids[agent],
                    length=len(missing_pids[agent]),
                    verbose=progress
                )
            else:
                progress_bar = progressbar(
                    items=agent_class.get_all_pids(),
                    length=counts[agent],
                    verbose=progress
                )
            for pid in progress_bar:
                if enqueue:
                    task = task_mef_from_agent.delay(
                        pid=pid,
                        agent=agent,
                        dbcommit=True,
                        reindex=True,
                        online=online
                    )
                    if verbose:
                        click.echo(f'{agent} pid: {pid} task:{task}')
                else:
                    msg = task_mef_from_agent(
                        pid=pid,
                        agent=agent,
                        dbcommit=True,
                        reindex=True,
                        online=online
                    )
                    if verbose:
                        click.echo(msg)
            if wait:
                from ..cli import wait_empty_tasks
                wait_empty_tasks(delay=3, verbose=True)
                click.secho(
                    f'COUNTS: mef: {counts["mef"]}|{AgentMefRecord.count()}'
                    f', {agent}: {counts[agent]}|{agent_class.count()}',
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
    click.secho(f'  Create VIAF CSV files.', err=True)
    pidstore = os.path.join(output_directory, 'viaf_pidstore.csv')
    metadata = os.path.join(output_directory, 'viaf_metadata.csv')
    click.secho(
        f'  VIAF input file: {viaf_file} ',
        err=True
    )

    count = create_viaf_files(
        viaf_input_file=viaf_file,
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
    click.secho(f'  Create MEF CSV files from JSON.', err=True)
    pidstore = os.path.join(output_directory, 'mef_pidstore.csv')
    metadata = os.path.join(output_directory, 'mef_metadata.csv')
    ids = os.path.join(output_directory, 'mef_id.csv')

    click.secho(
        f'  VIAF input file: {viaf_metadata_file} ',
        err=True
    )
    message = f'  CSV output files: {pidstore}, {metadata}'

    count = create_mef_files(
            viaf_pidstore_file=viaf_metadata_file,
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
