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

"""Celery tasks to index records."""

import click
from celery import shared_task
from flask import current_app

from .api import ReroMefIndexer
from .utils import get_agent_class


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
    return ReroMefIndexer(version_type=version_type).process_bulk_queue(
        es_bulk_kwargs=es_bulk_kwargs, stats_only=stats_only)


@shared_task(ignore_result=True)
def index_record(record_uuid):
    """Index a single record.

    :param record_uuid: The record UUID.
    """
    return ReroMefIndexer().index_by_id(record_uuid)


@shared_task(ignore_result=True)
def delete_record(record_uuid):
    """Delete a single record.

    :param record_uuid: The record UUID.
    """
    return ReroMefIndexer().delete_by_id(record_uuid)


@shared_task(ignore_result=True)
def mef_viaf_record(pid, agent, dbcommit=False, reindex=False):
    """Create or update MEF and VIAF record.

    :param record: the record for which a MEF and VIAF record is to be created
    :param dbcommit: commit changes to db
    :param reindex: reindex the records
    """
    record_class = get_agent_class(agent)
    if record_class:
        record = record_class.get_record_by_pid(pid)
        if record:
            return record.create_or_update_mef_viaf_record(
                dbcommit=True,
                reindex=True
            )


@shared_task
def create_or_update(index, record, agent, dbcommit=True, reindex=True,
                     online=False, test_md5=False, verbose=False):
    """Create or update record task.

    :param index: index of record
    :param record: record data to use
    :param agent: agent to use
    :param dbcommit: db commit or not
    :param reindex: reindex or not
    :param test_md5: test md5 or not
    :param verbose: verbose or not
    :returns: id type, pid or id, agent action, mef action
    """
    agent_class = get_agent_class(agent)
    returned_record, agent_action = agent_class.create_or_update(
        data=record, dbcommit=dbcommit, reindex=reindex, test_md5=test_md5
    )
    if agent in ['aidref', 'aggnd', 'agrero']:
        if agent_action.CREATE:
            mef_record, mef_action, viaf_record, got_online = returned_record.\
                create_or_update_mef_viaf_record(
                    dbcommit=dbcommit,
                    reindex=reindex,
                    online=online
                )
    id = returned_record.get('pid')
    id_type = 'pid :'
    if not id:
        id_type = 'uuid:'
        id = returned_record.id
    if verbose:
        message = '{index:<10} {agent} {type} {id} {agent_action}'.format(
            index=index,
            agent=agent,
            type=id_type,
            id=str(id),
            agent_action=agent_action.name
        )
        if agent_action.CREATE and agent in ['aidref', 'aggnd', 'agrero']:
            message += ' mef: {m_pid} {m_action} |' \
                       ' viaf: {v_pid} {online}'.format(
                            m_pid=mef_record.pid,
                            m_action=mef_action.name,
                            v_pid=viaf_record.pid,
                            online=got_online
                       )
        click.echo(message)
    return id_type, str(id), str(agent_action)


@shared_task
def delete(index, pid, agent, dbcommit=True, delindex=True, verbose=False):
    """Delete record task.

    :param index: index of record
    :param pid: pid to delete
    :param agent: agent to use
    :param dbcommit: db commit or not
    :param delindex: delete index or not
    :param verbose: verbose or not
    :returns: action
    """
    agent_class = get_agent_class(agent)
    agent_record = agent_class.get_record_by_pid(pid)
    action = None
    if agent_record:
        result, action = agent_record.delete(dbcommit=dbcommit,
                                             delindex=delindex)
        if verbose:
            message = '{index:<10} Deleted {agent} {pid:<38} {action}'.format(
                index=index,
                agent=agent,
                pid=pid,
                action=action
            )
            current_app.logger.info(message)
    else:
        message = '{index:<10} Not found {agent} {pid:<38}'.format(
            index=index,
            agent=agent,
            pid=pid,
        )
        current_app.logger.warning(message)
    return action
