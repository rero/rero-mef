# RERO MEF
# Copyright (C) 2026 RERO
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

import contextlib
import os
import tempfile
import time
import uuid

import click
from flask import current_app
from flask.cli import with_appcontext
from sqlitedict import SqliteDict

from ..cli import wait_empty_tasks
from ..cli_logging import ensure_single_stream_handler
from ..utils import (
    get_entity_classes,
    number_records_in_file,
    progressbar,
    read_json_record,
)
from .api import get_all_missing_viaf_pids, get_unlinked_agents
from .tasks import task_create_mef_and_agents_from_viaf
from .utils import create_mef_files, create_viaf_files
from .viaf.api import AgentViafRecord
from .viaf.tasks import (
    process_viaf_refresh,
    viaf_get_record,
)


def _clean_non_existing_viaf_links(non_existing_pids, verbose=False):
    """Remove stale VIAF links from MEF records.

    :param non_existing_pids: Mapping ``mef_pid -> viaf_pid`` to clean.
    :param verbose: Verbose output.
    :returns: Number of MEF records cleaned.
    """
    from .mef.api import AgentMefRecord

    cleaned = 0
    for mef_pid, viaf_pid in non_existing_pids.items():
        if not (mef_record := AgentMefRecord.get_record_by_pid(mef_pid)):
            if verbose:
                click.echo(f"  Missing MEF record: {mef_pid} (viaf_pid={viaf_pid})")
            continue

        if mef_record.get("viaf_pid") != viaf_pid:
            if verbose:
                click.echo(
                    f"  Skip MEF {mef_pid}: viaf_pid changed "
                    f"({mef_record.get('viaf_pid')} != {viaf_pid})"
                )
            continue

        mef_record.pop("viaf_pid", None)
        mef_record.update(data=mef_record, dbcommit=True, reindex=True)
        cleaned += 1
        if verbose:
            click.echo(f"  Cleaned MEF {mef_pid}: removed viaf_pid {viaf_pid}")
    return cleaned


@click.group()
def agents():
    """Agent management commands."""
    ensure_single_stream_handler()


@agents.command()
@click.option(
    "-k",
    "--enqueue",
    "enqueue",
    is_flag=True,
    default=False,
    help="Enqueue record creation.",
)
@click.option("-o", "--online", "online", multiple=True, default=[])
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@click.option("-V", "--online_verbose", "online_verbose", is_flag=True, default=False)
@click.option("-p", "--progress", "progress", is_flag=True, default=False)
@click.option("-w", "--wait", "wait", is_flag=True, default=False)
@click.option("-f", "--viaf_file", "viaf_file", type=click.File("r"), default=None)
@with_appcontext
def create_from_viaf(
    enqueue,
    online,
    verbose,
    online_verbose,
    progress,
    wait,
    viaf_file,
):
    """Create MEF and agents from viaf."""
    ensure_single_stream_handler()

    def get_pids_from_json(json_file):
        """Get all pids from JSON file."""
        for record in read_json_record(json_file):
            yield record["pid"]

    click.secho("Create MEF and Agency from VIAF.", fg="green")
    non_existing_pids = {}
    agent_classes = get_entity_classes(without_mef_viaf=False)
    counts = {
        name: {"old": agent_class.count()}
        for name, agent_class in agent_classes.items()
    }

    if viaf_file:
        progress_bar = progressbar(
            items=get_pids_from_json(viaf_file),
            length=number_records_in_file(viaf_file.name, "json"),
            verbose=progress,
            label="VIAF file",
        )
    else:
        progress_bar = progressbar(
            items=AgentViafRecord.get_all_pids(),
            length=counts["viaf"]["old"],
            verbose=progress,
            label="VIAF create MEF",
        )
    _, non_existing_pids = get_all_missing_viaf_pids(verbose=verbose)
    click.echo("Create MEF and agents from VIAF")
    for pid in progress_bar:
        if enqueue:
            task = task_create_mef_and_agents_from_viaf.delay(
                pid=pid, dbcommit=True, reindex=True, online=online
            )
            click.echo(f"viaf pid: {pid} task:{task}")
        else:
            task_create_mef_and_agents_from_viaf(
                pid=pid,
                dbcommit=True,
                reindex=True,
                online=online,
                verbose=verbose,
                online_verbose=online_verbose,
            )

    if non_existing_pids:
        click.echo(f"Clean VIAF pids from MEF records: {len(non_existing_pids)}")
        cleaned = _clean_non_existing_viaf_links(
            non_existing_pids=non_existing_pids,
            verbose=verbose,
        )
        click.echo(f"Cleaned MEF records: {cleaned}")

    if wait:
        wait_empty_tasks(delay=3, verbose=True)
        for name, agent_class in get_entity_classes(without_mef_viaf=False).items():
            counts[name]["new"] = agent_class.count()
        counts.pop("viaf", None)
        msgs = [f"mef: {counts['mef']['old']}|{counts['mef']['new']}"]
        counts.pop("mef", None)
        msgs.extend(
            f"{agent}: {value['old']}|{counts[agent]['new']}"
            for agent, value in counts.items()
        )

        click.secho(f"COUNTS: {', '.join(msgs)}", fg="blue")


@agents.command()
@click.argument("viaf_file")
@click.argument("output_directory")
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@with_appcontext
def create_csv_viaf(viaf_file, output_directory, verbose):
    """Create VIAF CSV from VIAF source text file.

    :param viaf_file: VIAF source text file.
    :param output_directory: Output directory.
    :param verbose: Verbose.
    """
    click.secho("  Create VIAF CSV files.", err=True)
    pidstore = os.path.join(output_directory, "viaf_pidstore.csv")
    metadata = os.path.join(output_directory, "viaf_metadata.csv")
    click.secho(f"  VIAF input file: {viaf_file}", err=True)

    count = create_viaf_files(
        viaf_input_file_name=viaf_file,
        viaf_pidstore_file_name=pidstore,
        viaf_metadata_file_name=metadata,
        verbose=verbose,
    )
    click.secho(f"  Number of VIAF records created: {count}.", fg="green", err=True)


@agents.command()
@click.argument("viaf_metadata_file")
@click.argument("output_directory")
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@with_appcontext
def create_csv_mef(viaf_metadata_file, output_directory, verbose):
    """Create MEF CSV from INVENIO metadata file.

    :param viaf_metadata_file: VIAF metadata CSV file.
    :param output_directory: Output directory.
    :param verbose: Verbose.
    """
    click.secho("  Create MEF CSV files from VIAF metadata.", err=True)
    pidstore = os.path.join(output_directory, "mef_pidstore.csv")
    metadata = os.path.join(output_directory, "mef_metadata.csv")
    ids = os.path.join(output_directory, "mef_id.csv")

    click.secho(f"  VIAF input file: {viaf_metadata_file}", err=True)
    # message = f'  CSV output files: {pidstore}, {metadata}'

    count = create_mef_files(
        viaf_metadata_file_name=viaf_metadata_file,
        input_directory=output_directory,
        mef_pidstore_file_name=pidstore,
        mef_metadata_file_name=metadata,
        mef_ids_file_name=ids,
        verbose=verbose,
    )

    click.secho(f"  Number of MEF records created: {count}.", fg="green", err=True)


@agents.command()
@click.option(
    "-b",
    "--batch_size",
    "batch_size",
    default=0,
    type=click.IntRange(min=0),
    help="Limit number of records to process (0=all).",
)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@click.option("-p", "--progress", "progress", is_flag=True, default=False)
@click.option(
    "-d",
    "--delete-if-not-found",
    "delete_if_not_found",
    is_flag=True,
    default=False,
    help="Delete old VIAF record if redirect target not found or fails.",
)
@click.option(
    "-P", "--pid", "viaf_pid", default=None, help="Harvest a single VIAF PID."
)
@click.option(
    "-U",
    "--unlinked",
    "unlinked",
    is_flag=True,
    default=False,
    help="Search VIAF online for agents without a VIAF link.",
)
@click.option("-V", "--online_verbose", "online_verbose", is_flag=True, default=False)
@click.option(
    "-u",
    "--update-agents",
    "update_agents",
    is_flag=True,
    default=False,
    help="Update MEF and agent records (GND/IdRef) after each VIAF update.",
)
@click.option(
    "--delay",
    "delay",
    default=1.0,
    type=float,
    help="Seconds to wait between VIAF fetch requests (default: 1).",
)
@with_appcontext
def harvest_viaf(
    batch_size,
    verbose,
    progress,
    delete_if_not_found,
    viaf_pid,
    unlinked,
    online_verbose,
    update_agents,
    delay,
):
    """Harvest and refresh VIAF records from the online API.

    Fetches VIAF cluster data via the JSON API and updates local records
    using MD5 change detection. Handles cluster merges (redirects)
    automatically. Processes records oldest-first.

    With --unlinked, searches VIAF online for MEF agents that have no VIAF
    link and creates or updates the corresponding VIAF records.
    """
    # Normalize batch_size: 0 means "all records"
    batch_arg = None if batch_size == 0 else batch_size

    if unlinked:
        if batch_arg is not None:
            raise click.UsageError("--unlinked cannot be combined with --batch_size")

        click.secho("Search VIAF for agents without VIAF link.", fg="green")
        app = current_app._get_current_object()
        processed = 0

        def _fetch_viaf(mef_pid, viaf_source_code, entity_pid):
            """Fetch a single VIAF record online and return result tuple.

            :param mef_pid: MEF record PID.
            :param viaf_source_code: VIAF source code (e.g. DNB, SUDOC).
            :param entity_pid: Agent PID to look up in VIAF.
            :returns: Tuple (mef_pid, viaf_source_code, entity_pid, data, msg).
            """
            from .viaf.api import RetryableVIAFError

            with app.app_context():
                try:
                    data, msg = AgentViafRecord.get_online_record(
                        viaf_source_code=viaf_source_code,
                        pid=entity_pid,
                    )
                except RetryableVIAFError as e:
                    return mef_pid, viaf_source_code, entity_pid, None, str(e)
                return mef_pid, viaf_source_code, entity_pid, data, msg

        db_path = os.path.join(
            tempfile.gettempdir(), f"viaf_unlinked_{uuid.uuid4().hex}.sqlite"
        )
        try:
            with SqliteDict(db_path, autocommit=True) as task_dict:
                for mef_pid, viaf_source_code, entity_pid in get_unlinked_agents(
                    relink=True, dbcommit=True, reindex=True, progress=progress
                ):
                    task_dict[mef_pid] = (viaf_source_code, entity_pid)

                progress_bar = progressbar(
                    items=task_dict,
                    length=len(task_dict),
                    verbose=progress,
                    label="VIAF lookup",
                )
                for mef_pid in progress_bar:
                    viaf_source_code, entity_pid = task_dict[mef_pid]
                    processed += 1
                    if delay:
                        time.sleep(delay)
                    mef_pid, viaf_source_code, entity_pid, data, msg = _fetch_viaf(
                        mef_pid, viaf_source_code, entity_pid
                    )
                    if online_verbose:
                        click.echo(f"  {msg}")
                    if not data:
                        if "NO RECORD" in msg:
                            if verbose:
                                click.echo(
                                    f"  No VIAF found for mef:{mef_pid} {viaf_source_code}:{entity_pid}"
                                )
                        else:
                            click.secho(
                                f"  VIAF lookup failed for mef:{mef_pid} {viaf_source_code}:{entity_pid}: {msg}",
                                fg="red",
                                err=True,
                            )
                        continue
                    if data.get("NO TRANSFORMATION") or not data.get("pid"):
                        if verbose:
                            click.echo(
                                f"  Invalid VIAF data for mef:{mef_pid} {viaf_source_code}:{entity_pid}: {msg}"
                            )
                        continue
                    viaf_pid_new = data["pid"]
                    viaf_record, _ = AgentViafRecord.create_or_update(
                        data=data, dbcommit=True, reindex=True
                    )
                    if verbose and viaf_record:
                        click.echo(
                            f"  mef_pid: {mef_pid} linked viaf_pid: {viaf_pid_new}"
                        )
        finally:
            with contextlib.suppress(OSError):
                os.remove(db_path)
        click.echo(f"Processed {processed} MEF records without VIAF link.")
        return

    if viaf_pid:
        if batch_arg is not None:
            raise click.UsageError("--pid cannot be combined with --batch_size")

        click.secho(f"VIAF single record harvest: {viaf_pid}", fg="green")
        action = viaf_get_record(
            viaf_pid=viaf_pid,
            verbose=verbose,
            progress=progress,
            delete_if_not_found=delete_if_not_found,
            update_agents=update_agents,
        )
        click.secho(f"Processed: {viaf_pid}", fg="green")
        click.echo(f"  {action}")
        return

    click.secho("VIAF refresh.", fg="green")
    count, action_counts = process_viaf_refresh(
        batch_size=batch_arg,
        verbose=verbose,
        progress=progress,
        delete_if_not_found=delete_if_not_found,
        update_agents=update_agents,
    )
    click.secho(f"Processed: {count}", fg="green")
    for action, cnt in action_counts.items():
        click.echo(f"  {action}: {cnt}")
