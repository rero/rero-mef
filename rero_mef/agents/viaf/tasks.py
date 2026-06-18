# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Celery tasks for VIAF cluster refresh."""

import contextlib

# For persistent batching
import os
import tempfile
import uuid

import click
from celery import shared_task
from sqlitedict import SqliteDict

from ...api import Action
from ...extensions import MD5Extension
from ...utils import progressbar, set_timestamp
from .api import (
    AgentViafRecord,
    AgentViafSearch,
    RetryableVIAFError,
    _get_redirect_pid_from_msg,
)

_md5 = MD5Extension()


def _refresh_viaf_record(
    pid,
    dbcommit=True,
    reindex=True,
    verbose=False,
    delete_if_not_found=False,
    update_agents=False,
):
    """Fetch a VIAF record online and update if changed.

    :param pid: VIAF PID to refresh.
    :param dbcommit: Commit changes to DB.
    :param reindex: Reindex record.
    :param verbose: Print verbose messages.
    :param delete_if_not_found: Delete old record if redirect target not found.
    :param update_agents: Update MEF and agent records (GND/IdRef) after VIAF update.
    :returns: Action performed.
    """
    try:
        online_data, msg = AgentViafRecord.get_online_record(
            viaf_source_code="VIAF", pid=pid
        )
    except RetryableVIAFError as err:
        if verbose:
            click.echo(str(err))
            click.echo(f"  VIAF {pid}: {Action.ERROR.value}")
        return Action.ERROR
    if verbose:
        click.echo(msg)

    # Handle redirect (VIAF cluster merge)
    if redirect_to_pid := _get_redirect_pid_from_msg(msg):
        if existing_record := AgentViafRecord.get_record_by_pid(pid):
            _new_record, action, _redirect_info = existing_record.handle_redirect(
                redirect_to_pid=redirect_to_pid,
                dbcommit=dbcommit,
                reindex=reindex,
                delete_if_not_found=delete_if_not_found,
            )
            if verbose:
                click.echo(f"  VIAF {pid} -> {redirect_to_pid}: {action.value}")
            return action

        try:
            online_data, msg = AgentViafRecord.get_online_record(
                viaf_source_code="VIAF", pid=redirect_to_pid
            )
        except RetryableVIAFError as err:
            if verbose:
                click.echo(str(err))
                click.echo(f"  VIAF {pid} -> {redirect_to_pid}: {Action.ERROR.value}")
            return Action.ERROR
        if verbose:
            click.echo(msg)
        if _get_redirect_pid_from_msg(msg):
            if verbose:
                click.echo(f"  VIAF {pid} -> {redirect_to_pid}: {Action.ERROR.value}")
            return Action.ERROR

    if not online_data:
        if verbose:
            click.echo(f"  VIAF {pid}: not found online")
        return Action.NOT_FOUND

    # Standard create or update with MD5 change detection
    online_data = _md5.add_md5(online_data)
    viaf_record, action = AgentViafRecord.create_or_update(
        data=online_data,
        dbcommit=dbcommit,
        reindex=reindex,
        test_md5=True,
    )
    if verbose:
        click.echo(f"  VIAF {pid}: {action.value}")

    if action in (Action.CREATE, Action.UPDATE, Action.REPLACE):
        viaf_record.create_mef_and_agents(dbcommit=dbcommit, reindex=reindex)

    if action == Action.UPTODATE and dbcommit:
        # Touch _updated so this record moves to the back of the queue.
        # Without this, unchanged records stay at the front and are re-fetched
        # every cycle instead of cycling through all records.
        viaf_record.commit()
        viaf_record.dbcommit(reindex=reindex)

    if update_agents and action == Action.UPTODATE:
        # Force-sync agents even though VIAF data is unchanged — useful after
        # a bug fix in agent processing without needing to modify VIAF records.
        # update_viaf=True: also search VIAF online for displaced agents.
        actions = viaf_record.create_mef_and_agents(
            dbcommit=dbcommit, reindex=reindex, update_viaf=True
        )
        if verbose:
            click.echo(f"  VIAF {pid}: agents force-updated {actions}")

    return action


@shared_task
def process_viaf_refresh(
    batch_size=None,
    dbcommit=True,
    reindex=True,
    verbose=False,
    progress=False,
    delete_if_not_found=False,
    update_agents=False,
):
    """Refresh of oldest VIAF records.

    Processes a batch of VIAF records ordered by _updated (oldest first).
    Designed to be run daily to gradually refresh all records over a
    configurable cycle (default ~6 months).

    :param batch_size: Number of records per batch (None=get all).
    :param dbcommit: Commit changes to DB.
    :param reindex: Reindex records.
    :param verbose: Print verbose messages.
    :param progress: Display progress bar.
    :param delete_if_not_found: Delete old record if redirect target not found.
    :param update_agents: Update MEF and agent records (GND/IdRef) after VIAF update.
    :returns: Tuple (count, action_counts).
    """
    action_counts = {}

    # Use a persistent SqliteDict to store PIDs for this batch

    tmpdir = tempfile.gettempdir()
    db_path = os.path.join(tmpdir, f"viaf_refresh_pids_{uuid.uuid4().hex}.sqlite")

    # Only fetch and store PIDs if the DB is empty (first run or after cleanup)
    try:
        with SqliteDict(db_path, autocommit=True) as pid_dict:
            if not pid_dict:
                # Query oldest-updated VIAF records, fetch only PIDs
                query = (
                    AgentViafSearch().sort({"_updated": {"order": "asc"}}).source("pid")
                )
                # Estimate total for progress bar (if possible)
                total = AgentViafRecord.count()
                if batch_size is not None:
                    total = min(batch_size, total)
                progress_bar = progressbar(
                    items=query.scan(),
                    length=total,
                    verbose=progress,
                    label="VIAF PID collect",
                )
                for count, hit in enumerate(progress_bar):
                    if batch_size is not None and count >= batch_size:
                        break
                    pid_dict[hit.pid] = 1

            # Process all PIDs in the dict (they are only the ones needed for this batch)
            progress_bar = progressbar(
                items=pid_dict,
                length=len(pid_dict),
                verbose=progress,
                label="VIAF refresh",
            )
            count = 0
            for pid in progress_bar:
                action = _refresh_viaf_record(
                    pid=pid,
                    dbcommit=dbcommit,
                    reindex=reindex,
                    verbose=verbose,
                    delete_if_not_found=delete_if_not_found,
                    update_agents=update_agents,
                )
                action_counts.setdefault(action, 0)
                action_counts[action] += 1
                count += 1

            AgentViafRecord.flush_indexes()
            result = (count, {k.value: v for k, v in action_counts.items()})
            set_timestamp("viaf__refresh", count=count, action_counts=result[1])
            return result
    finally:
        # Always clean up the DB file at the end, even on crash
        with contextlib.suppress(OSError):
            os.remove(db_path)


@shared_task
def viaf_get_record(
    viaf_pid,
    dbcommit=True,
    reindex=True,
    verbose=False,
    progress=False,
    delete_if_not_found=False,
    update_agents=False,
):
    """Fetch and update a single VIAF record from the online API.

    :param viaf_pid: VIAF PID to fetch.
    :param dbcommit: Commit changes to DB.
    :param reindex: Reindex record.
    :param verbose: Print verbose messages.
    :param progress: Display progress information.
    :param delete_if_not_found: Delete old record if redirect target not found.
    :param update_agents: Update MEF and agent records (GND/IdRef) after VIAF update.
    :returns: Action performed.
    """
    action = _refresh_viaf_record(
        pid=viaf_pid,
        dbcommit=dbcommit,
        reindex=reindex,
        verbose=verbose,
        delete_if_not_found=delete_if_not_found,
        update_agents=update_agents,
    )
    return action.value
