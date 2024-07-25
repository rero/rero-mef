# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2024 RERO
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

from __future__ import absolute_import, print_function

import itertools
import json
import os
import sys
from time import sleep

import click
import redis
import yaml
from celery import current_app as current_celery
from flask import current_app
from flask.cli import with_appcontext
from flask_security.confirmable import confirm_user
from invenio_accounts.cli import commit, users
from invenio_db import db
from invenio_oaiharvester.cli import oaiharvester
from invenio_oaiharvester.models import OAIHarvestConfig
from invenio_oauth2server.cli import process_scopes, process_user
from invenio_oauth2server.models import Client, Token
from invenio_records_rest.utils import obj_or_import_string
from sqlitedict import SqliteDict
from werkzeug.local import LocalProxy
from werkzeug.security import gen_salt

from .marctojson.records import RecordsCount
from .monitoring.api import Monitoring
from .tasks import create_or_update as task_create_or_update
from .tasks import delete as task_delete
from .tasks import process_bulk_queue as task_process_bulk_queue
from .utils import (
    JsonWriter,
    add_md5,
    add_oai_source,
    bulk_load_ids,
    bulk_load_metadata,
    bulk_load_pids,
    bulk_save_ids,
    bulk_save_metadata,
    bulk_save_pids,
    create_csv_file,
    export_json_records,
    get_entity_class,
    get_entity_indexer_class,
    number_records_in_file,
    oai_get_last_run,
    oai_set_last_run,
    progressbar,
    read_json_record,
)

_datastore = LocalProxy(lambda: current_app.extensions["security"].datastore)


def abort_if_false(ctx, param, value):
    """Abort command is value is False."""
    if not value:
        ctx.abort()


@click.group()
def fixtures():
    """Fixtures management commands."""


@click.group()
def utils():
    """Misc management commands."""


@click.group()
def celery():
    """Celery management commands."""


@fixtures.command()
@click.argument("entity")
@click.argument("source", type=click.File("r"), default=sys.stdin)
@click.option("-l", "--lazy", "lazy", is_flag=True, default=False)
@click.option(
    "-5",
    "--md5",
    "test_md5",
    is_flag=True,
    default=False,
    help="Compaire md5 to find out if we have to update",
)
@click.option(
    "-k",
    "--enqueue",
    "enqueue",
    is_flag=True,
    default=False,
    help="Enqueue record creation.",
)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@with_appcontext
def create_or_update(entity, source, lazy, test_md5, enqueue, verbose):
    """Create or update entity records.

    :param entity: entity to create or update.
    :param source: File with entities data in JSON format.
    :param lazy: lazy reads file
    :param test_md5: Compaire md5 to find out if we have to update.
    :param online: Try to get VIAF online if not exist.
    :param verbose: Verbose.
    """
    click.secho(f"Update records: {entity}", fg="green")
    if lazy:
        # try to lazy read JSON file (slower, better memory management)
        data = read_json_record(source)
    else:
        data = json.load(source)
        if isinstance(data, dict):
            data = [data]

    for idx, record in enumerate(data, 1):
        if enqueue:
            task_create_or_update.delay(
                idx=idx,
                record=record,
                entity=entity,
                dbcommit=True,
                reindex=True,
                test_md5=test_md5,
                verbose=verbose,
            )
        else:
            task_create_or_update(
                idx=idx,
                record=record,
                entity=entity,
                dbcommit=True,
                reindex=True,
                test_md5=test_md5,
                verbose=verbose,
            )


@fixtures.command()
@click.argument("entity")
@click.argument("source", type=click.File("r"), default=sys.stdin)
@click.option("-l", "--lazy", "lazy", is_flag=True, default=False)
@click.option(
    "-k",
    "--enqueue",
    "enqueue",
    is_flag=True,
    default=False,
    help="Enqueue record deletion.",
)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@with_appcontext
def delete(entity, source, lazy, enqueue, verbose):
    """Delete entity records.

    :param entity: Entity to delete.
    :param source: File with entity data in JSON format.
    :param lazy: lazy reads file
    :param verbose: Verbose.
    """
    click.secho(f"Delete records: {entity}", fg="red")
    if lazy:
        # try to lazy read JSON file (slower, better memory management)
        data = read_json_record(source)
    else:
        data = json.load(source)
        if isinstance(data, dict):
            data = [data]

    for idx, record in enumerate(data, 1):
        if enqueue:
            task_delete.delay(
                idx=idx,
                pid=record.get("pid"),
                entity=entity,
                dbcommit=True,
                delindex=True,
                verbose=verbose,
            )
        else:
            pid = record.get("pid")
            task_delete(
                idx=idx,
                pid=pid,
                entity=entity,
                dbcommit=True,
                delindex=True,
                verbose=verbose,
            )


@fixtures.command()
@click.argument("entity")
@click.argument("marc_file")
@click.argument("json_file")
@click.option("-e", "--error_file", "error_file", default=None, type=click.File("wb"))
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@with_appcontext
def marc_to_json(entity, marc_file, json_file, error_file, verbose):
    """Entity MARC to JSON.

    :param entity: entity [aidref, aggnd, agrero, coidref, cognd, corero, plidref, plgnd].
    :param marc_file: MARC input file.
    :param json_file: JSON output file.
    :param verbose: Verbose.
    """
    json_deleted_file_name = (
        f"{os.path.splitext(json_file)[0]}" f"_deleted{os.path.splitext(json_file)[-1]}"
    )
    click.secho(
        f" Transform {entity} MARC to JSON. " f"{json_file} {json_deleted_file_name}",
        err=True,
    )
    json_file = JsonWriter(json_file)
    json_deleted_file = JsonWriter(json_deleted_file_name)

    count_created = 0
    count_deleted = 0

    transformation = current_app.config.get("TRANSFORMATION")
    records = []
    try:
        records = RecordsCount(str(marc_file))
    except Exception as err:
        click.secho(f"Marc file not found for {entity}:{err}", fg="red", err=True)

    pids = {}
    count_errors = 0
    for record, count in records:
        data = transformation[entity](
            marc=record, logger=current_app.logger, verbose=True
        )
        if json_data := data.json:
            if msg := json_data.get("NO TRANSFORMATION"):
                if verbose:
                    pid = json_data.get("pid", "???")
                    click.secho(f"  {pid} NO TRANSFORMATION: {msg}", fg="yellow")
            else:
                pid = json_data.get("pid")
                if pids.get(pid):
                    click.secho(
                        f"  {count:8} Error duplicate pid in {entity}: {pid}", fg="red"
                    )
                else:
                    pids[pid] = 1
                    add_md5(json_data)
                    if json_data.get("deleted"):
                        count_deleted += 1
                        json_deleted_file.write(json_data)
                    else:
                        count_created += 1
                        json_file.write(json_data)
        else:
            count_errors += 1
            if error_file:
                error_file.write(record.as_marc())
            click.secho(f"{count:8} Error transformation MARC {entity}", fg="yellow")

    json_file.close()
    json_deleted_file.close()

    click.secho(
        f"  Number of {entity} JSON records created: {count_created}.",
        fg="green",
        err=True,
    )
    if count_deleted:
        click.secho(
            f"  Number of {entity} JSON records deleted: {count_deleted}.",
            fg="yellow",
            err=True,
        )
    if count_errors:
        click.secho(
            f"  Number of {entity} MARC records errors: {count_errors}.",
            fg="red",
            err=True,
        )


@fixtures.command()
@click.argument("entity")
@click.argument("json_file")
@click.argument("output_directory")
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@with_appcontext
def create_csv(entity, json_file, output_directory, verbose):
    """Entity create CSV files.

    :param entity: entity [aidref, aggnd, agrero, corero].
    :param json_file: JSON input file.
    :param output_directory: Output directory.
    :param verbose: Verbose.
    :param ids: Create IDs file.
    """
    click.secho(f"  Create {entity} CSV files from JSON.", err=True)
    pidstore = os.path.join(output_directory, f"{entity}_pidstore.csv")
    metadata = os.path.join(output_directory, f"{entity}_metadata.csv")
    click.secho(f"  JSON input file: {json_file} ", err=True)
    message = f"  CSV output files: {pidstore}, {metadata}"
    if entity == "mef":
        ids = os.path.join(output_directory, "mef_id.csv")
        message += f", {ids}"
    click.secho(message, err=True)

    count = create_csv_file(json_file, entity, pidstore, metadata)

    click.secho(f"  Number of {entity} records created: {count}.", fg="green", err=True)


@fixtures.command()
@click.argument("entity")
@click.argument("pidstore_file")
@click.argument("metadata_file")
@click.option("-i", "--ids_file", "ids_file", help="IDs file to load.")
@click.option(
    "-c",
    "--bulk_count",
    "bulk_count",
    default=0,
    type=int,
    help="Set the bulk load chunk size.",
)
@click.option(
    "-r",
    "--reindex",
    "reindex",
    help="add record to reindex.",
    is_flag=True,
    default=False,
)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@with_appcontext
def load_csv(
    entity, pidstore_file, metadata_file, ids_file, bulk_count, reindex, verbose
):
    """Entity load CSV.

    :param entity: entity [aidref, aggnd, agrero, corero, viaf, mef].
    :param pidstore_file: Pidstore file to load.
    :param metadata_file: Metadata_file to load.
    :param ids_file: IDs file to load.
    :param last_run_file: File with last run date.
    :param bulk_count: Set the bulk load chunk size.
    :param reindex: add record to reindex.
    :param verbose: Verbose.
    """
    click.secho(f"Load {entity} CSV files into database.", err=True)
    click.secho(f"  CSV input files: {pidstore_file}|{metadata_file} ", err=True)

    click.secho(
        "  Number of records in pidstore to load: "
        f'{number_records_in_file(pidstore_file, "csv")}.',
        fg="green",
        err=True,
    )
    bulk_load_pids(entity, pidstore_file, bulk_count=bulk_count, verbose=verbose)

    click.secho(
        f"  Number of records in metadata to load: "
        f'{number_records_in_file(metadata_file, "csv")}.',
        fg="green",
        err=True,
    )
    bulk_load_metadata(
        entity, metadata_file, bulk_count=bulk_count, verbose=verbose, reindex=reindex
    )
    if ids_file:
        click.secho(
            "  Number of records in id to load: "
            f'{number_records_in_file(ids_file, "csv")}',
            fg="green",
            err=True,
        )
        try:
            bulk_load_ids(entity, ids_file, bulk_count=bulk_count, verbose=verbose)
        except Exception as err:
            click.secho(f"Error: {err}", fg="red")
        # TODO: get entity identifier
        # append_fixtures_new_identifiers(MefIdentifier, [], 'mef')


@fixtures.command()
@click.argument("output_directory")
@click.option(
    "-e",
    "--entity",
    "entities",
    multiple=True,
    default=[
        "aggnd",
        "aidref",
        "agrero",
        "mef",
        "viaf",
        "cidref",
        "corero",
        "comef",
        "pidref",
        "plmef",
    ],
)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@with_appcontext
def save_csv(entities, output_directory, verbose):
    """Entity record dump.

    :param output_directory: Output directory.
    :param entities: entity to export.
        default=['aggnd', 'aidref', 'agrero', 'mef', 'viaf',
                 'cidref', 'corero', 'comef', 'pidref', 'plgnd', 'plmef'])
    :param verbose: Verbose.
    """
    oai_names = {
        "aggnd": "agents.gnd",
        "aidref": "agents.idref",
        "cidref": "concepts.idref",
        "pidref": "places.idref",
    }
    for entity in entities:
        click.secho(
            f"Save {entity} CSV files to directory: {output_directory}", fg="green"
        )
        file_name = os.path.join(output_directory, f"{entity}_metadata.csv")
        if verbose:
            click.echo(f"  Save metadata: {file_name}")
        bulk_save_metadata(entity, file_name=file_name, verbose=False)
        file_name = os.path.join(output_directory, f"{entity}_pidstore.csv")
        if verbose:
            click.echo(f"  Save pidstore: {file_name}")
        bulk_save_pids(entity, file_name=file_name, verbose=False)
        if last_run := oai_get_last_run(oai_names.get(entity)):
            file_name = os.path.join(output_directory, f"{entity}_last_run.txt")
            if verbose:
                click.echo(f"  Save last run: {file_name}")
            with open(file_name, "w") as last_run_file:
                last_run_file.write(f"{last_run}")
    if entity in ["mef", "comef", "plmef"]:
        file_name = os.path.join(output_directory, "mef_id.csv")
        if verbose:
            click.echo(f"  Save ID: {file_name}")
        bulk_save_ids(entity, file_name=file_name, verbose=False)


@fixtures.command()
@click.argument("csv_metadata_file")
@click.argument("json_output_file")
@click.option("-I", "--indent", "indent", type=click.INT, default=2)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@with_appcontext
def csv_to_json(csv_metadata_file, json_output_file, indent, verbose):
    """Entities record dump.

    :param csv_metadata_file: CSV metadata file.
    :param json_output_file: JSON output file.
    :param indent: indent for output
    :param verbose: Verbose.
    """
    click.secho(
        f"CSV to JSON transform: {csv_metadata_file} -> {json_output_file}", fg="green"
    )
    with open(csv_metadata_file) as metadata_file:
        output_file = JsonWriter(json_output_file, indent=indent)
        length = number_records_in_file(csv_metadata_file, "csv")
        progress_bar = progressbar(
            items=metadata_file, length=length, label="Transform:", verbose=verbose
        )
        for count, metadata_line in enumerate(progress_bar, 1):
            data = json.loads(metadata_line.split("\t")[3])
            if verbose:
                click.echo(f'{count:<10}: {data["pid"]}\t{data}')
            output_file.write(data)


@fixtures.command()
@click.argument("csv_metadata_file")
@click.option(
    "-c", "-csv_metadata_file_compair", "csv_metadata_file_compair", default=None
)
@click.option("-e", "--entity", "entity", default=None)
@click.option("-o", "--output", "output", is_flag=True, default=False)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@click.option("-s", "--sqlite_dict", "sqlite_dict", default="sqlite_dict.db")
@with_appcontext
def csv_diff(
    csv_metadata_file, csv_metadata_file_compair, entity, output, verbose, sqlite_dict
):
    """Entities record diff.

    :param csv_metadata_file: CSV metadata file to compair.
    :param csv_metadata_file_compair: CSV metadata file to compair too.
    :param entity: entity type to compair too.
    :param verbose: Verbose.
    :param sqlite_dict: SqliteDict Db file name.
    """

    def get_pid_data(line):
        """Get JSON from CSV text line.

        :param line: line of CSV text.
        :returns: data as json
        """
        data = json.loads(line.split("\t")[3].replace("\\\\", "\\"))
        data.pop("md5", None)
        pid = data.get("pid")
        return pid, data

    if csv_metadata_file_compair and not entity:
        compair = csv_metadata_file_compair
    elif entity:
        compair = entity
    else:
        click.secho("One of -c or -e parameter mandatory", fg="red", err=True)
        sys.exit(1)
    click.secho(f"CSV diff: {compair} <-> {csv_metadata_file}", fg="green")
    if output:
        file_name = os.path.splitext(csv_metadata_file)[0]
        file_name_new = f"{file_name}_new.json"
        file_new = JsonWriter(file_name_new)
        file_name_diff = f"{file_name}_changed.json"
        file_diff = JsonWriter(file_name_diff)
        file_name_delete = f"{file_name}_delete.json"
        file_delete = JsonWriter(file_name_delete)
        click.echo(f"New     file: {file_name_new}")
        click.echo(f"Changed file: {file_name_diff}")
        click.echo(f"Deleted file: {file_name_delete}")

    counts = {
        "new": 0,
        "changed": 0,
        "unchanged": 0,
        "deleted": 0,
        "compair": 0,
        "compair_to": 0,
    }
    compair_data = {}
    if sqlite_dict:
        compair_data = SqliteDict(
            sqlite_dict, autocommit=False, outer_stack=False, journal_mode="OFF"
        )
        compair_data.clear()
        compair_data.commit()
    if csv_metadata_file_compair:
        length = number_records_in_file(csv_metadata_file_compair, "csv")
        counts["compair"] = length
        with open(csv_metadata_file_compair, "r", buffering=1) as meta_file:
            progress_bar = progressbar(
                items=meta_file,
                length=length,
                label=f"Loading: {compair}",
                verbose=True,
            )
            for idx, metadata_line in enumerate(progress_bar, 1):
                pid, data = get_pid_data(metadata_line)
                compair_data[pid] = data
                if sqlite_dict and idx % 1000 == 0:
                    compair_data.commit()
            if sqlite_dict:
                compair_data.commit()
    elif entity:
        entity_class = get_entity_class(entity)
        length = entity_class.count()
        counts["compair"] = length
        progress_bar = progressbar(
            items=entity_class.get_all_ids(),
            length=length,
            label=f"Loading entity: {compair}",
            verbose=True,
        )
        for id_ in progress_bar:
            if record := entity_class.get_record(id_):
                record.pop("md5", None)
                compair_data[record.pid] = record

    db.session.close()
    with open(csv_metadata_file, "r", buffering=1) as metadata_file:
        length = number_records_in_file(csv_metadata_file, "csv")
        counts["compair_to"] = length
        progress_bar = progressbar(
            items=metadata_file,
            length=length,
            label=f"Reading: {csv_metadata_file}",
            verbose=True,
        )
        for metadata_line in progress_bar:
            pid, data = get_pid_data(metadata_line)
            if existing_data := compair_data.pop(pid, None):
                if sqlite_dict:
                    compair_data.commit()
                if existing_data != data:
                    counts["changed"] += 1
                    if verbose:
                        click.echo("DIFF: ")
                        click.echo(
                            " old:\t" f"{json.dumps(existing_data, sort_keys=True)}"
                        )
                        click.echo(f" new:\t{json.dumps(data, sort_keys=True)}")
                    if output:
                        add_md5(data)
                        file_diff.write(data)
                else:
                    counts["unchanged"] += 1
                    if verbose:
                        click.echo("UNCHANGED: ")
                        click.echo(f"{json.dumps(existing_data, sort_keys=True)}")
            else:
                counts["new"] += 1
                if verbose:
                    click.echo(f"NEW :\t{json.dumps(data, sort_keys=True)}")
                if output:
                    add_md5(data)
                    file_new.write(data)
    for pid, data in compair_data.items():
        counts["deleted"] += 1
        if verbose:
            click.echo(f"DEL :\t{json.dumps(data, sort_keys=True)}")
        if output:
            add_md5(data)
            file_delete.write(data)
    file_new.close()
    file_diff.close()
    file_delete.close()
    if sqlite_dict:
        compair_data.close()
    click.echo(
        f'Compair: {counts["compair"]} | '
        f'Compair to: {counts["compair_to"]} || '
        f'Changed: {counts["changed"]} | '
        f'New: {counts["new"]} | '
        f'Deleted: {counts["deleted"]} | '
        f'Unchanged: {counts["unchanged"]} '
    )


@oaiharvester.command("addsource")
@click.argument("name")
@click.argument("baseurl")
@click.option(
    "-m", "--metadataprefix", default="marc21", help="The prefix for the metadata"
)
@click.option(
    "-s", "--setspecs", default="", help="The ‘set’ criteria for the harvesting"
)
@click.option("-c", "--comment", default="", help="Comment")
@click.option("-u", "--update", is_flag=True, default=False, help="Update config")
@with_appcontext
def add_oai_source_config(name, baseurl, metadataprefix, setspecs, comment, update):
    """Add OAIHarvestConfig.

    :param name: Name of OAI source.
    :param baseurl: Baseurl of OAI source.
    :param metadataprefix: The prefix for the metadata
    :param setspecs: The `set` criteria for the harvesting
    :param comment: Comment
    :param update: update config
    """
    click.echo(f"Add OAIHarvestConfig: {name} ", nl=False)
    msg = add_oai_source(
        name=name,
        baseurl=baseurl,
        metadataprefix=metadataprefix,
        setspecs=setspecs,
        comment=comment,
        update=update,
    )
    click.echo(msg)


@oaiharvester.command("initconfig")
@click.argument("configfile", type=click.File("rb"))
@click.option("-u", "--update", is_flag=True, default=False, help="Update config")
@with_appcontext
def init_oai_harvest_config(configfile, update):
    """Init OAIHarvestConfig."""
    configs = yaml.load(configfile, Loader=yaml.FullLoader)
    for name, values in sorted(configs.items()):
        baseurl = values["baseurl"]
        metadataprefix = values.get("metadataprefix", "marc21")
        setspecs = values.get("setspecs", "")
        comment = values.get("comment", "")
        click.echo(f"Add OAIHarvestConfig: {name} {baseurl} ", nl=False)
        msg = add_oai_source(
            name=name,
            baseurl=baseurl,
            metadataprefix=metadataprefix,
            setspecs=setspecs,
            comment=comment,
            update=update,
        )
        click.echo(msg)


@oaiharvester.command()
@with_appcontext
def schedules():
    """List harvesting schedules."""
    celery_ext = current_app.extensions.get("invenio-celery")
    for key, value in celery_ext.celery.conf.beat_schedule.items():
        click.echo(key + "\t", nl=False)
        click.echo(value)


@oaiharvester.command("info")
@with_appcontext
def oaiharvester_info():
    """List infos for tasks."""
    oais = OAIHarvestConfig.query.all()
    for oai in oais:
        click.echo(oai.name)
        click.echo(f"\tlastrun       : {oai.lastrun}")
        click.echo(f"\tbaseurl       : {oai.baseurl}")
        click.echo(f"\tmetadataprefix: {oai.metadataprefix}")
        click.echo(f"\tcomment       : {oai.comment}")
        click.echo(f"\tsetspecs      : {oai.setspecs}")


@oaiharvester.command()
@click.option(
    "-n", "--name", "name", default="", help="Name of persistent configuration to use."
)
@with_appcontext
def get_last_run(name):
    """Gets the lastrun for a OAI harvest configuration."""
    return oai_get_last_run(name=name, verbose=True)


@oaiharvester.command()
@click.option(
    "-n", "--name", default="", help="Name of persistent configuration to use."
)
@click.option("-d", "--date", default=None, help="Last date to set for the harvesting.")
@with_appcontext
def set_last_run(name, date):
    """Sets the lastrun for a OAI harvest configuration."""
    return oai_set_last_run(name=name, date=date, verbose=True)


@oaiharvester.command()
@click.option(
    "-n", "--name", default=None, help="Name of persistent configuration to use."
)
@click.option(
    "-f",
    "--from-date",
    default=None,
    help="The lower bound date for the harvesting (optional).",
)
@click.option(
    "-t",
    "--until_date",
    default=None,
    help="The upper bound date for the harvesting (optional).",
)
@click.option(
    "-a",
    "--arguments",
    default=[],
    multiple=True,
    help="Arguments to harvesting task, in the form `-a arg1=val1`.",
)
@click.option("-q", "--quiet", is_flag=True, default=False, help="Supress output.")
@click.option(
    "-k",
    "--enqueue",
    is_flag=True,
    default=False,
    help="Enqueue harvesting and return immediately.",
)
@click.option(
    "-5",
    "--md5",
    "test_md5",
    is_flag=True,
    default=False,
    help="Compaire md5 to find out if we have to update",
)
@click.option(
    "-o",
    "--viaf_online",
    "viaf_online",
    is_flag=True,
    default=False,
    help="Get online VIAF record if missing",
)
@click.option(
    "-d",
    "--debug",
    "debug",
    is_flag=True,
    default=False,
    help="Print debug informations",
)
@with_appcontext
def harvestname(
    name, from_date, until_date, arguments, quiet, enqueue, test_md5, debug, viaf_online
):
    """Harvest records from an OAI repository.

    :param name: Name of persistent configuration to use.
    :param from-date: The lower bound date for the harvesting (optional).
    :param until_date: The upper bound date for the harvesting (optional).
    :param arguments: Arguments to harvesting task, in the form
                       `-a arg1=val1`.
    :param quiet: Supress output.
    :param enqueue: Enqueue harvesting and return immediately.
    :param test_md5: Compaire md5 to find out if we have to update.
    :param viaf_online: Get online VIAF record if missing.
    """
    click.secho(f"Harvest {name} ...", fg="green")
    arguments = dict(x.split("=", 1) for x in arguments)
    try:
        harvest_task = obj_or_import_string(
            f"rero_mef.{name}.tasks:process_records_from_dates"
        )
    except Exception:
        oai_names = [oai.name for oai in OAIHarvestConfig.query.all()]
        click.secho(f'Config "{name}" not found in {oai_names}', fg="red", err=True)
        sys.exit(1)
    count = 0
    action_count = {}
    mef_action_count = {}
    if harvest_task:
        if enqueue:
            job = harvest_task.delay(
                from_date=from_date,
                until_date=until_date,
                test_md5=test_md5,
                verbose=(not quiet),
                debug=debug,
                viaf_online=viaf_online,
                **arguments,
            )
            click.echo(f"Scheduled job {job.id}")
        else:
            count, action_count, mef_action_count = harvest_task(
                from_date=from_date,
                until_date=until_date,
                test_md5=test_md5,
                verbose=(not quiet),
                debug=debug,
                viaf_online=viaf_online,
                **arguments,
            )
            actions = ", ".join(
                [f"{action.value}={count}" for action, count in action_count.items()]
            )
            mef_actions = ", ".join(
                [
                    f"{action.value}={count}"
                    for action, count in mef_action_count.items()
                ]
            )
            click.echo(f"Count: {count} agent: {actions} mef: {mef_actions}")


@oaiharvester.command()
@click.argument("output_file_name")
@click.option(
    "-n", "--name", default=None, help="Name of persistent configuration to use."
)
@click.option(
    "-f",
    "--from-date",
    default=None,
    help="The lower bound date for the harvesting (optional).",
)
@click.option(
    "-t",
    "--until_date",
    default=None,
    help="The upper bound date for the harvesting (optional).",
)
@click.option("-q", "--quiet", is_flag=True, default=False, help="Supress output.")
@click.option(
    "-k",
    "--enqueue",
    is_flag=True,
    default=False,
    help="Enqueue harvesting and return immediately.",
)
@with_appcontext
def save(output_file_name, name, from_date, until_date, quiet, enqueue):
    """Harvest records from an OAI repository and save to file.

    :param name: Name of persistent configuration to use.
    :param from-date: The lower bound date for the harvesting (optional).
    :param until_date: The upper bound date for the harvesting (optional).
    :param quiet: Supress output.
    :param enqueue: Enqueue harvesting and return immediately.
    """
    click.secho(f"Harvest: {name} {output_file_name} ...", fg="green")
    # TODO: addapt to other entity types
    save_task = obj_or_import_string(f"rero_mef.{name}.tasks:save_records_from_dates")
    count = 0
    if save_task:
        if enqueue:
            job = save_task.delay(
                file_name=output_file_name,
                from_date=from_date,
                until_date=until_date,
                verbose=(not quiet),
            )
            click.echo(f"Scheduled job {job.id}")
        else:
            count = save_task(
                file_name=output_file_name,
                from_date=from_date,
                until_date=until_date,
                verbose=(not quiet),
            )
            click.echo(f"Count: {count}")


@utils.command()
@click.argument("output_path")
@click.option(
    "-t",
    "--pid-type",
    "pid_type",
    multiple=True,
    default=[
        "aggnd",
        "aidref",
        "agrero",
        "mef",
        "viaf",
        "cidref",
        "corero",
        "comef",
        "pidref",
        "plmef",
    ],
)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@click.option("-I", "--indent", "indent", type=click.INT, default=2)
@click.option("-s", "--schema", "schema", is_flag=True, default=False)
@with_appcontext
def export(output_path, pid_type, verbose, indent, schema):
    """Export multiple records into JSON format.

    :param pid_type: record type
    :param verbose: verbose
    :param pidfile: files with pids to extract
    :param indent: indent for output
    :param schema: do not delete $schema
    """
    for p_type in pid_type:
        output_file_name = os.path.join(output_path, f"{p_type}.json")
        click.secho(f"Export {p_type} records: {output_file_name}", fg="green")
        record_class = obj_or_import_string(
            current_app.config.get("RECORDS_REST_ENDPOINTS")
            .get(p_type)
            .get("record_class")
        )
        export_json_records(
            pids=record_class.get_all_pids(),
            pid_type=p_type,
            output_file_name=output_file_name,
            indent=indent,
            schema=schema,
            verbose=verbose,
        )


@utils.command("runindex")
@click.option("--delayed", "-d", is_flag=True, help="Run indexing in background.")
@click.option(
    "--concurrency",
    "-c",
    default=1,
    type=int,
    help="Number of concurrent indexing tasks to start.",
)
@click.option(
    "--with_stats",
    is_flag=True,
    default=False,
    help="report number of successful and list failed error response.",
)
@click.option(
    "--queue",
    "-q",
    type=str,
    help="Name of the celery queue used to put the tasks into.",
)
@click.option("--version-type", help="Elasticsearch version type to use.")
@click.option(
    "--raise-on-error/--skip-errors",
    default=True,
    help=("Controls if Elasticsearch bulk indexing" " errors raises an exception."),
)
@with_appcontext
def run(
    delayed, concurrency, with_stats, version_type=None, queue=None, raise_on_error=True
):
    """Run bulk record indexing.

    :param delayed: Run indexing in background.
    :param concurrency: Number of concurrent indexing tasks to start.
    :param queue: Name of the celery queue used to put the tasks into.
    :param version-type: Elasticsearch version type to use.
    :param raise-on-error: 'Controls if Elasticsearch bulk indexing.
    """
    celery_kwargs = {
        "kwargs": {
            "version_type": version_type,
            "search_bulk_kwargs": {"raise_on_error": raise_on_error},
            "stats_only": not with_stats,
        }
    }
    if delayed:
        click.secho(f"Starting {concurrency} tasks for indexing records...", fg="green")
        if queue is not None:
            celery_kwargs["queue"] = queue
        for _ in range(concurrency):
            process_id = task_process_bulk_queue.delay(
                version_type=version_type,
                search_bulk_kwargs={"raise_on_error": raise_on_error},
                stats_only=not with_stats,
            )
            click.secho(f"index async: {process_id}", fg="yellow")
    else:
        click.secho("Indexing records...", fg="green")
        indexed, error = task_process_bulk_queue(
            version_type=version_type,
            search_bulk_kwargs={"raise_on_error": raise_on_error},
            stats_only=not with_stats,
        )
        click.secho(f"indexed: {indexed}, error: {error}", fg="yellow")


@utils.command()
@click.option(
    "--yes-i-know",
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt="Do you really want to reindex all records?",
)
@click.option("-t", "--pid_type", "pid_type", multiple=True, required=True)
@click.option("-n", "--no-info", "no_info", is_flag=True, default=True)
@with_appcontext
def reindex(pid_type, no_info):
    """Reindex all records.

    :param pid_type: Pid type Could be multiples pid types.
    :param no-info: No `runindex` information displayed after execution.
    """
    for p_type in pid_type:
        click.secho(f"Sending {p_type} to indexing queue ...", fg="green")
        entity_class = get_entity_class(p_type)
        entity_indexer = get_entity_indexer_class(p_type)
        entity_indexer().bulk_index(entity_class.get_all_ids())
    if no_info:
        click.secho('Execute "runindex" command to process the queue!', fg="yellow")


def queue_count():
    """Count tasks in celery."""
    inspector = current_celery.control.inspect()
    task_count = 0
    reserved = inspector.reserved()
    if reserved:
        for values in reserved.values():
            task_count += len(values)
    active = inspector.active()
    if active:
        for values in active.values():
            task_count += len(values)
    return task_count


def wait_empty_tasks(delay, verbose=False):
    """Wait for tasks to be empty."""
    if verbose:
        spinner = itertools.cycle(["-", "\\", "|", "/"])
        click.echo(f"Waiting: {next(spinner)}\r", nl=False)
    # TODO: we have to find a way do get the remaining queue count from
    # rabbitmq. The cellery queue could be empty but not the rabbitmq
    # queue. try to get the queue count twice with a delay of 5 seconds
    # to be more sure the cellery and rabbitmy queue is empty.
    count = queue_count()
    sleep(5)
    count += queue_count()
    while count:
        if verbose:
            click.echo(f"Waiting: {next(spinner)}\r", nl=False)
        sleep(delay)
        count = queue_count()
        sleep(5)
        count += queue_count()


@celery.command()
@with_appcontext
def celery_task_count():
    """Count entries in celery tasks."""
    click.secho(f"Celery tasks active: {queue_count()}", fg="green")


@celery.command()
@click.option("-d", "--delay", "delay", default=3)
@with_appcontext
def wait_empty_tasks_cli(delay):
    """Wait for tasks to be empty."""
    wait_empty_tasks(delay=delay, verbose=True)
    click.secho("No active celery tasks.", fg="green")


@utils.command()
@click.option(
    "--yes-i-know",
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt="Do you really want to flush the redis cache?",
)
@with_appcontext
def flush_cache():
    """Flush the redis cache."""
    red = redis.StrictRedis.from_url(current_app.config["CACHE_REDIS_URL"])
    red.flushall()
    click.secho("Redis cache cleared!", fg="red")


@users.command("confirm")
@click.argument("user")
@with_appcontext
@commit
def manual_confirm_user(user):
    """Confirm a user."""
    user_obj = _datastore.get_user(user)
    if user_obj is None:
        raise click.UsageError("ERROR: User not found.")
    if confirm_user(user_obj):
        click.secho(f'User "{user}" has been confirmed.', fg="green")
    else:
        click.secho(f'User "{user}" was already confirmed.', fg="yellow")


@utils.command()
@click.option(
    "-e",
    "--entity",
    "entities",
    multiple=True,
    default=[
        "aggnd",
        "aidref",
        "agrero",
        "mef",
        "viaf",
        "cidref",
        "corero",
        "comef",
        "pidref",
        "plmef",
    ],
)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@with_appcontext
def reindex_missing(entities, verbose):
    """Reindex entities missing in ES.

    :param entities: entity type to compair too.
    :param verbose: Verbose.
    """
    for entity in entities:
        click.secho(f"Reindex missing {entity} from ES.", fg="green")
        entity_class = get_entity_class(entity)
        pids_es, pids_db, pids_es_double, index = Monitoring().get_es_db_missing_pids(
            doc_type=entity, verbose=verbose
        )
        if verbose:
            click.secho(
                f"  {entity} ES: {len(pids_es)} DB: {len(pids_db)} "
                f"Double:{len(pids_es_double)}"
            )
            progress_bar = progressbar(items=pids_db, length=len(pids_db), verbose=True)
            for pid in progress_bar:
                if rec := entity.get_record_by_pid(pid):
                    rec.reindex()
                else:
                    click.secho(f"  {entity} record not found: {pid}", fg="red")


def create_personal(name, user_id, scopes=None, is_internal=False, access_token=None):
    """Create a personal access token.

    A token that is bound to a specific user and which doesn't expire, i.e.
    similar to the concept of an API key.

    :param name: Client name.
    :param user_id: User ID.
    :param scopes: The list of permitted scopes. (Default: ``None``)
    :param is_internal: If ``True`` it's a internal access token.
            (Default: ``False``)
    :param access_token: personalized access_token.
    :returns: A new access token.
    """
    with db.session.begin_nested():
        scopes = " ".join(scopes) if scopes else ""

        client = Client(
            name=name,
            user_id=user_id,
            is_internal=True,
            is_confidential=False,
            _default_scopes=scopes,
        )
        client.gen_salt()

        if not access_token:
            access_token = gen_salt(
                current_app.config.get("OAUTH2SERVER_TOKEN_PERSONAL_SALT_LEN")
            )
        token = Token(
            client_id=client.client_id,
            user_id=user_id,
            access_token=access_token,
            expires=None,
            _scopes=scopes,
            is_personal=True,
            is_internal=is_internal,
        )

        db.session.add(client)
        db.session.add(token)

    return token


@utils.command("tokens_create")
@click.option("-n", "--name", required=True)
@click.option(
    "-u", "--user", required=True, callback=process_user, help="User ID or email."
)
@click.option("-s", "--scope", "scopes", multiple=True, callback=process_scopes)
@click.option("-i", "--internal", is_flag=True)
@click.option(
    "-t",
    "--access_token",
    "access_token",
    required=False,
    help="personalized access_token.",
)
@with_appcontext
def tokens_create(name, user, scopes, internal, access_token):
    """Create a personal OAuth token."""
    token = create_personal(
        name, user.id, scopes=scopes, is_internal=internal, access_token=access_token
    )
    db.session.commit()
    click.secho(token.access_token, fg="blue")
