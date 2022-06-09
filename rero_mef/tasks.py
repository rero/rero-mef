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

from .api import ReroIndexer
from .utils import get_entity_class


@shared_task(ignore_result=True)
def process_bulk_queue(version_type=None, es_bulk_kwargs=None,
                       stats_only=True):
    """Process bulk indexing queue.

    :param str version_type: Elasticsearch version type.
    :param dict es_bulk_kwargs: Passed to
        :func:`elasticsearch:elasticsearch.helpers.bulk`.
    :param boolean stats_only: if `True` only report number of
            successful/failed operations instead of just number of
            successful and a list of error responses.
    Note: You can start multiple versions of this task.
    """
    return ReroIndexer(version_type=version_type).process_bulk_queue(
        es_bulk_kwargs=es_bulk_kwargs, stats_only=stats_only)


@shared_task(ignore_result=True)
def index_record(record_uuid):
    """Index a single record.

    :param record_uuid: The record UUID.
    """
    return ReroIndexer().index_by_id(record_uuid)


@shared_task(ignore_result=True)
def delete_record(record_uuid):
    """Delete a single record.

    :param record_uuid: The record UUID.
    """
    return ReroIndexer().delete_by_id(record_uuid)


@shared_task(ignore_result=True)
def mef_viaf_record(pid, agent, dbcommit=False, reindex=False):
    """Create or update MEF and VIAF record.

    :param record: the record for which a MEF and VIAF record is to be created
    :param dbcommit: commit changes to db
    :param reindex: reindex the records
    """
    if record_class := get_entity_class(agent):
        if record := record_class.get_record_by_pid(pid):
            return record.create_or_update_mef_viaf_record(
                dbcommit=True,
                reindex=True
            )


@shared_task
def create_or_update(index, record, entity, dbcommit=True, reindex=True,
                     online=False, test_md5=False, verbose=False):
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
    returned_record, agent_action = entity_class.create_or_update(
        data=record, dbcommit=dbcommit, reindex=reindex, test_md5=test_md5
    )
    if entity in ['aidref', 'aggnd', 'agrero'] and agent_action.CREATE:
        mef_record, mef_action, viaf_record, got_online = returned_record.\
            create_or_update_mef_viaf_record(
                dbcommit=dbcommit,
                reindex=reindex,
                online=online
            )
    pid = returned_record.get('pid')
    id_type = 'pid :'
    if not rec_id:
        id_type = 'uuid:'
        rec_id = returned_record.id
    if verbose:
        msg = f'{index:<10} {entity} {id_type} {rec_id} {agent_action.name}'
        if agent_action.CREATE and entity in ['aidref', 'aggnd', 'agrero']:
            if viaf_record:
                v_pid = viaf_record['pid']
            msg += (f' mef: {mef_record.pid} {mef_action.name} |'
                    f' viaf: {v_pid} {got_online}')
        click.echo(msg)
    return id_type, str(pid), str(agent_action)


@shared_task
def delete(index, pid, entity, dbcommit=True, delindex=True, verbose=False):
    """Delete record task.

    :param index: index of record
    :param pid: pid to delete
    :param agent: agent to use
    :param dbcommit: db commit or not
    :param delindex: delete index or not
    :param verbose: verbose or not
    :returns: action
    """
    agent_class = get_entity_class(entity)
    agent_record = agent_class.get_record_by_pid(pid)
    action = None
    if agent_record:
        _, action = agent_record.delete(dbcommit=dbcommit, delindex=delindex)
        if verbose:
            click.echo(f'{index:<10} Deleted {entity} {pid:<38} {action}')
    else:
        current_app.logger.warning(f'{index:<10} Not found {entity} {pid:<38}')
    return action
