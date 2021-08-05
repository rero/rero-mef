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

"""Tasks used by  RERO-MEF."""

from celery import shared_task

from .viaf.api import AgentViafRecord
from ..utils import get_entity_class


@shared_task
def task_create_mef_from_viaf_agent(pid, dbcommit=True, reindex=True,
                                    test_md5=False, online=False,
                                    verbose=False):
    """Create MEF and agents from VIAF task.

    :param pid: pid for VIAF to use
    :param dbcommit: db commit or not
    :param reindex: reindex or not
    :param test_md5: test md5 or not
    :param online: get missing records from internet
    :param verbose: verbose or not
    :returns: string with pid and actions
    """
    viaf_record = AgentViafRecord.get_record_by_pid(pid)
    actions = viaf_record.create_mef_and_agents(
        dbcommit=dbcommit,
        reindex=reindex,
        test_md5=test_md5,
        online=online,
        verbose=verbose
    )
    return actions


@shared_task
def task_create_mef_for_agent(pid, agent, dbcommit=True, reindex=True,
                              online=False):
    """Create MEF from agent task.

    :param pid: pid for agent to use
    :param agent: agent
    :param dbcommit: db commit or not
    :param reindex: reindex or not
    :param online: get VIAF online if not exist
    :returns: no return
    """
    agent_class = get_entity_class(agent)
    agent_record = agent_class.get_record_by_pid(pid)
    if agent_record:
        mef_record, mef_action, viaf_record, online = \
            agent_record.create_or_update_mef_viaf_record(
                dbcommit=dbcommit,
                reindex=reindex,
                online=online
            )
        mef_pid = 'Non'
        if mef_record:
            mef_pid = mef_record.pid
        viaf_pid = 'Non'
        if viaf_record:
            viaf_pid = viaf_record.pid

        actions = f'mef: {mef_pid} {mef_action.value} ' \
            'viaf: {viaf_pid} {online}'
        return f'Create MEF from {agent} pid: {pid} | {actions}'
    else:
        return f'Not found agent {agent}:{pid}'
