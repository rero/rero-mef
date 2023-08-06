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

"""Celery tasks to index records."""

import click
from celery import shared_task
from flask import current_app

from .api import Action, ReroIndexer
from .utils import get_entity_class


@shared_task(ignore_result=True)
def process_bulk_queue(version_type=None, search_bulk_kwargs=None,
                       stats_only=True):
    """Process bulk indexing queue.

    :param str version_type: Elasticsearch version type.
    :param dict search_bulk_kwargs: Passed to
        :func:`elasticsearch:elasticsearch.helpers.bulk`.
    :param boolean stats_only: if `True` only report number of
            successful/failed operations instead of just number of
            successful and a list of error responses.
    Note: You can start multiple versions of this task.
    """
    return ReroIndexer(version_type=version_type).process_bulk_queue(
        search_bulk_kwargs=search_bulk_kwargs, stats_only=stats_only)


@shared_task
def create_or_update(idx, record, entity, dbcommit=True, reindex=True,
                     test_md5=False, verbose=False):
    """Create or update record task.

    :param index: index of record
    :param record: record data to use
    :param agent: agent to use
    :param dbcommit: db commit or not
    :param reindex: reindex or not
    :param test_md5: test md5 or not
    :param verbose: verbose or not
    :returns: id type, pid or id, agent action, MEF action
    """
    entity_class = get_entity_class(entity)
    record, agent_action = entity_class.create_or_update(
        data=record, dbcommit=dbcommit, reindex=reindex, test_md5=test_md5)
    entities = current_app.config.get('RERO_ENTITIES', [])
    mef_record = None
    if entity in entities and \
            agent_action in (Action.CREATE, Action.UPDATE, Action.REPLACE):
        mef_record, mef_actions = record.create_or_update_mef(
            dbcommit=dbcommit, reindex=reindex)
    rec_id = record.get('pid')
    id_type = 'pid:'
    if not rec_id:
        id_type = 'uuid:'
        rec_id = record.id
    if verbose:
        msg = (
            f'{idx:<10} {entity:<6} {id_type:<5} {rec_id:<25} '
            f'{agent_action.name}'
        )
        if mef_record:
            for mef_pid, mef_action in mef_actions.items():
                msg = f'{msg} | mef: {mef_pid} {mef_action.name}'
        click.echo(msg)
    return id_type, str(rec_id), agent_action


@shared_task
def delete(idx, pid, entity, dbcommit=True, delindex=True, verbose=False):
    """Delete record task.

    :param index: index of record
    :param pid: pid to delete
    :param agent: agent to use
    :param dbcommit: db commit or not
    :param delindex: delete index or not
    :param verbose: verbose or not
    :returns: action
    """
    entity_class = get_entity_class(entity)
    if entity_record := entity_class.get_record_by_pid(pid):
        entity_record.delete(dbcommit=dbcommit, delindex=delindex)
        if verbose:
            msg = f'{idx:<10} {entity:<6} pid: {pid:<25} DELETED'
            click.echo(msg)
        return 'DELETED: {entity} {pid}'
    msg = f'{idx:<10} {entity:<6} pid: {pid:<25} NOT FOUND'
    if verbose:
        click.secho(msg, fg='yellow')
    current_app.logger.warning(msg)
    return f'DELETE NOT FOUND: {entity} {pid}'
