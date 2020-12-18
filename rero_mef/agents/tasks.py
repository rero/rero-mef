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

from ..utils import get_agent_class
from ..viaf.api import ViafRecord


@shared_task
def create_mef_and_agents_from_viaf(pid, dbcommit=True, reindex=True,
                                    test_md5=False, online=False,
                                    verbose=False):
    """Create MEF and agents from VIAF task.

    :param pid: pid for viaf to use
    :param dbcommit: db commit or not
    :param reindex: reindex or not
    :param test_md5: test md5 or not
    :param online: get missing records from internet
    :param verbose: verbose or not
    :returns: string with pid and actions
    """
    viaf_record = ViafRecord.get_record_by_pid(pid)
    actions = viaf_record.create_mef_and_agents(
        dbcommit=dbcommit,
        reindex=reindex,
        test_md5=test_md5,
        online=online,
        verbose=verbose
    )
    return actions


@shared_task
def create_mef_from_agent(pid, agent, dbcommit=True, reindex=True,
                          online=False):
    """Create MEF from agent task.

    :param pid: pid for agent to use
    :param agent: agent
    :param dbcommit: db commit or not
    :param reindex: reindex or not
    :param test_md5: test md5 or not
    :param online: get viaf online if not exist
    :returns: no return
    """
    agent_class = get_agent_class(agent)
    agent_record = agent_class.get_record_by_pid(pid)
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

    actions = 'mef: {m_pid} {m_action} viaf: {v_pid} {online}'.format(
        m_pid=mef_pid,
        m_action=mef_action.value,
        v_pid=viaf_pid,
        online=online
    )

    msg = 'Create MEF from {agent} pid: {pid} | {actions}'.format(
        agent=agent,
        pid=pid,
        actions=actions
    )
    return msg
