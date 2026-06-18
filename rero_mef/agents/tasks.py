# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tasks used by  RERO-MEF."""

import click
from celery import shared_task

from .viaf.api import AgentViafRecord


@shared_task
def task_create_mef_and_agents_from_viaf(
    pid, dbcommit=True, reindex=True, online=None, verbose=False, online_verbose=False
):
    """Create MEF and agents from VIAF task.

    :param pid: pid for VIAF to use
    :param dbcommit: db commit or not
    :param reindex: reindex or not
    :param online: get missing records from internet
    :param verbose: verbose or not
    :param online_verbose: online verbose or not
    :returns: string with pid and actions
    """
    online = online or []
    if viaf_record := AgentViafRecord.get_record_by_pid(pid):
        return viaf_record.create_mef_and_agents(
            dbcommit=dbcommit,
            reindex=reindex,
            online=online,
            verbose=verbose,
            online_verbose=online_verbose,
        )
    click.secho(f"VIAF not found: {pid}", fg="red")
    return {}, {}
