# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2021 RERO
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

"""Click command line interface for MEF record management."""

from __future__ import absolute_import, print_function

import click
from flask import current_app
from flask.cli import with_appcontext

from .mef.api import ConceptMefRecord
from .tasks import task_create_mef_for_concept
from ..utils import get_entity_class, progressbar


@click.group()
def concepts():
    """Agent management commands."""


@concepts.command()
@click.option('-t', '--pid_type', 'pid_type', multiple=True,
              default=['corero', 'cidref'])
@click.option('-k', '--enqueue', 'enqueue', is_flag=True, default=False,
              help="Enqueue record creation.")
@click.option('-o', '--online', 'online', is_flag=True, default=False)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-p', '--progress', 'progress', is_flag=True, default=False)
@click.option('-w', '--wait', 'wait', is_flag=True, default=False)
@click.option('-m', '--missing', 'missing', is_flag=True, default=False)
@with_appcontext
def create_mef(pid_type, enqueue, online, verbose, progress, wait, missing):
    """Create MEF from concepts."""
    concepts = current_app.config.get('RERO_CONCEPTS', [])
    if missing:
        missing_pids, to_much_pids = \
            ConceptMefRecord.get_all_missing_pids(pid_type, verbose=progress)
    for concept in pid_type:
        if concept not in concepts:
            click.secho(
                f'Error create MEF from {concept}. Wrong concept!',
                fg='red'
            )
        else:
            click.secho(
                f'Create MEF from {concept}.',
                fg='green'
            )
            concept_class = get_entity_class(concept)
            counts = {
                concept: concept_class.count(),
                'mef': ConceptMefRecord.count()
            }
            if missing:
                progress_bar = progressbar(
                    items=missing_pids[concept],
                    length=len(missing_pids[concept]),
                    verbose=progress
                )
            else:
                progress_bar = progressbar(
                    items=concept_class.get_all_pids(),
                    length=counts[concept],
                    verbose=progress
                )
            for pid in progress_bar:
                if enqueue:
                    task = task_create_mef_for_concept.delay(
                        pid=pid,
                        concept=concept,
                        dbcommit=True,
                        reindex=True,
                        online=online
                    )
                    if verbose:
                        click.echo(f'{concept} pid: {pid} task:{task}')
                else:
                    msg = task_create_mef_for_concept(
                        pid=pid,
                        concept=concept,
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
                    f'COUNTS: mef: {counts["mef"]}|{ConceptMefRecord.count()}'
                    f', {concept}: {counts[concept]}|{concept_class.count()}',
                    fg='blue'
                )
