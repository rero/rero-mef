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

import itertools
from time import sleep

import click
from celery.bin.control import inspect
from flask.cli import with_appcontext

from .mef.api import AgentMefRecord
from .tasks import \
    create_mef_and_agents_from_viaf as task_mef_and_agents_from_viaf
from .tasks import create_mef_from_agent as task_mef_from_agent
from .viaf.api import AgentViafRecord
from ..monitoring import Monitoring
from ..utils import get_agent_class, get_agent_classes, progressbar


@click.group()
def utils():
    """Misc management commands."""


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
        task_count = sum(active.values())
    return task_count


def wait_empty_tasks(delay, verbose=False):
    """Wait for tasks to be empty."""
    if verbose:
        spinner = itertools.cycle(['-', '\\', '|', '/'])
        click.echo(
            f'Waiting: {next(spinner)}\r',
            nl=False
        )
    count = queue_count()
    sleep(5)
    count += queue_count()
    while count:
        if verbose:
            click.echo(
                f'Waiting: {next(spinner)}\r',
                nl=False
            )
        sleep(delay)
        count = queue_count()
        sleep(5)
        count += queue_count()


@utils.command('create_mef_and_agents_from_viaf')
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
def create_mef_and_agents_from_viaf(test_md5, enqueue, online, verbose,
                                    progress, wait, missing):
    """Create Mef and agents from viaf."""
    click.secho(
        'Create MEF and Agency from VIAF.',
        fg='green'
    )
    counts = {}
    agent_classes = get_agent_classes(without_mef_viaf=False)
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
        wait_empty_tasks(delay=3, verbose=True)
        for name, agent_class in get_agent_classes(
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


@utils.command('create_mef_from_agent')
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
def create_mef_from_agent(pid_type, enqueue, online, verbose, progress, wait,
                          missing):
    """Create Mef from agents."""
    if missing:
        missing_pids, to_much_pids = AgentMefRecord.get_all_missing_agents_pids(
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
            agent_class = get_agent_class(agent)
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
                wait_empty_tasks(delay=3, verbose=True)
                click.secho(
                    f'COUNTS: mef: {counts["mef"]}|{AgentMefRecord.count()}'
                    f', {agent}: {counts[agent]}|{agent_class.count()}',
                    fg='blue'
                )


@utils.command('reindex_missing')
@click.option('-a', '--agents', 'agents', multiple=True,
              default=['aggnd', 'aidref', 'agrero', 'mef', 'viaf', 'corero'])
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def reindex_missing(agents, verbose):
    """Reindex agents missing in ES."""
    for agent in agents:
        click.secho(
            f'Reindex missing {agent} from ES.',
            fg='green'
        )
        agent_class = get_agent_class(agent)
        pids_es, pids_db, pids_es_double, index = \
            Monitoring.get_es_db_missing_pids(doc_type=agent, verbose=verbose)
        if verbose:
            click.secho(
                f'  {agent} ES: {len(pids_es)} DB: {len(pids_db)} '
                f'Double:{len(pids_es_double)}'
            )
            progress_bar = progressbar(
                items=pids_db,
                length=len(pids_db),
                verbose=verbose
            )
            for pid in progress_bar:
                rec = agent_class.get_record_by_pid(pid)
                if rec:
                    rec.reindex()
                else:
                    click.secho(
                        f'  {agent} record not found: {pid}',
                        fg='red'
                    )
