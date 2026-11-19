# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Monitoring utilities."""

import click
from flask import current_app
from flask.cli import with_appcontext

from ..cli_logging import ensure_single_stream_handler
from .api import Monitoring


@click.group()
def monitoring():
    """Monitoring commands."""
    ensure_single_stream_handler()


@monitoring.command("dangling_pids")
@click.option("-d", "--delete", "delete", is_flag=True, default=False, help="delete the pids found")
@with_appcontext
def dangling_pids_cli(delete):
    """Print the pids resolving to no record, and optionally delete them.

    A record refused by its schema used to leave its minted pid behind, claimed and resolving to nothing, so the
    record could never be created again under it.
    """
    for doc_type in sorted(current_app.config.get("RECORDS_REST_ENDPOINTS", {})):
        pid_values = Monitoring.remove_dangling_pids(doc_type) if delete else Monitoring.get_dangling_pids(doc_type)
        if not pid_values:
            continue
        action = "deleted" if delete else "found"
        click.secho(f"{doc_type:>6} {len(pid_values):>6} {action}: {', '.join(pid_values)}", fg="red")


@monitoring.command("dangling_redirects")
@with_appcontext
def dangling_redirects_cli():
    """Print the `redirect_to` records whose target no record holds.

    Such a record forwards a request for its pid to a record nothing holds. IdRef's `redirect_from`, whose value
    is the superseded pid, is not reported.
    """
    found = 0
    for doc_type in sorted(current_app.config.get("RECORDS_REST_ENDPOINTS", {})):
        for pid, target in Monitoring.get_dangling_redirects(doc_type):
            click.secho(f"{doc_type:>6} {pid:>12} redirect_to {target}: target missing", fg="red")
            found += 1
    click.secho(f"dangling redirects: {found}", fg="red" if found else "green")


@monitoring.command("mef_counts")
@click.option(
    "-d",
    "--delay",
    "delay",
    default=1,
    help="Get ES and DB counts from delay minutes in the past.",
)
@with_appcontext
def mef_counts_cli(delay):
    """Print MEF counts.

    Prints a table representation of MEF counts. Columns: 1. MEF count minus database count 2. document type 3. database
    count 4. MEF count
    """
    mon = Monitoring(time_delta=delay)
    msg_head = f"MEF - DB  {'type':>6} {'DB':>10}  {'MEF':>10}"
    click.echo(msg_head)
    for entity, data in mon.check_mef().items():
        mef_db = data.get("mef-db", "")
        db_count = data.get("db", "")
        mef = data.get("mef", "")
        msg = f"{mef_db:>8}  {entity:>6} {db_count:>10}  {mef:>10}"
        if mef_db not in [0, ""]:
            click.secho(msg, fg="red")
        else:
            click.echo(msg)
