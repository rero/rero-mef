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
from flask import current_app
from flask.cli import with_appcontext

from .mef.api import AgentMefRecord
from .tasks import task_create_mef_for_agent, task_create_mef_from_viaf_agent
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
@click.option('-V', '--online_verbose', 'online_verbose', is_flag=True,
              default=False)
@click.option('-p', '--progress', 'progress', is_flag=True, default=False)
@click.option('-w', '--wait', 'wait', is_flag=True, default=False)
@click.option('-m', '--missing', 'missing', is_flag=True, default=False)
@with_appcontext
def create_from_viaf(test_md5, enqueue, online, verbose, online_verbose,
                     progress, wait, missing,):
    """Create MEF and agents from viaf."""
    click.secho(
        'Create MEF and Agency from VIAF.',
        fg='green'
    )
    unexisting_pids = {}
    agent_classes = get_entity_classes(without_mef_viaf=False)
    counts = {name: {'old': agent_class.count()}
              for name, agent_class in agent_classes.items()}

    if missing:
        missing_pids, unexisting_pids = AgentMefRecord. \
            get_all_missing_viaf_pids(
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
            task = task_create_mef_from_viaf_agent.delay(
                pid=pid,
                dbcommit=True,
                reindex=True,
                test_md5=test_md5,
                online=online
            )
            click.echo(f'viaf pid: {pid} task:{task}')
        else:
            task_create_mef_from_viaf_agent(
                pid=pid,
                dbcommit=True,
                reindex=True,
                test_md5=test_md5,
                online=online,
                verbose=verbose,
                online_verbose=online_verbose
            )

    if unexisting_pids:
        click.echo(
            f'Clean VIAF pids from MEF records: {len(unexisting_pids)}')
        for pid, viaf_pid in unexisting_pids.items():
            # TODO: clean MEF records with unexisting VIAF pids:
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
    agents = current_app.config.get('RERO_AGENTS', [])
    if missing:
        missing_pids, to_much_pids = \
            AgentMefRecord.get_all_missing_pids(pid_type, verbose=progress)
    for agent in pid_type:
        if agent not in agents:
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
            counts = {agent: agent_class.count()}
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
                    task = task_create_mef_for_agent.delay(
                        pid=pid,
                        agent=agent,
                        dbcommit=True,
                        reindex=True,
                        online=online
                    )
                    if verbose:
                        click.echo(f'{agent} pid: {pid} task:{task}')
                else:
                    msg = task_create_mef_for_agent(
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
    click.secho('  Create VIAF CSV files.', err=True)
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
    click.secho('  Create MEF CSV files from VIAF metadata.', err=True)
    pidstore = os.path.join(output_directory, 'mef_pidstore.csv')
    metadata = os.path.join(output_directory, 'mef_metadata.csv')
    ids = os.path.join(output_directory, 'mef_id.csv')

    click.secho(
        f'  VIAF input file: {viaf_metadata_file} ',
        err=True
    )
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


@agents.command()
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-c', '--commit', 'commit', is_flag=True, default=False)
@click.option('-t', '--pid_type', 'pid_type', multiple=True,
              default=['aidref', 'aggnd', 'agrero'])
@with_appcontext
def clean_multiple_viaf(verbose, commit, pid_type):
    """Clean multiple VIAF records.

    :param verbose: Verbose.
    :param commit: Commit changes.
    """
    click.secho('Clean multiple VIAF.')
    viaf_types_def = {
        'aidref': 'idref_pid',
        'aggnd': 'gnd_pid',
        'agrero': 'rero_pid'
    }
    viaf_types = []
    for p_type in pid_type:
        if v_type := viaf_types_def.get(p_type):
            viaf_types.append(v_type)
        else:
            click.secho(f'Unknown agent type: {p_type}.', fg='red')
    multiple_pids = AgentViafRecord.get_pids_with_multiple_viaf(
        record_types=viaf_types, verbose=verbose)
    for p_type in pid_type:
        if v_type := viaf_types_def.get(p_type):
            if verbose:
                click.echo(f'Cleaning {p_type}: {len(multiple_pids[v_type])}')
            agent_cls = get_entity_class(p_type)
            for pid, viaf_pids in multiple_pids[v_type].items():
                if rec := agent_cls.get_record_by_pid(pid):
                    if verbose:
                        click.echo(f'\t{rec.pid}')
                    for viaf_pid in viaf_pids:
                        if viaf := AgentViafRecord.get_record_by_pid(viaf_pid):
                            click.echo(f'\t\tDELETE VIAF: {viaf_pid}')
                            viaf.delete(dbcommit=commit, delindex=commit)
                    rec.create_or_update_mef_viaf_record(
                        dbcommit=commit, reindex=commit, online=commit)
