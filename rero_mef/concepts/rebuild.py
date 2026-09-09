# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Rebuild the concept MEF records on the normalised BNF association identifier.

The association identifiers live in the search index, so the concept records have to be reindexed before their MEF
records can be rebuilt on them. Nothing here changes the shape of the database, and it runs for hours over hundreds of
thousands of records, which is why it is a resumable command and not an alembic migration: alembic holds one
transaction open on its connection for the whole run, and a run long enough for the server to close that connection
loses every record it had already committed.
"""

import json

import click
from invenio_search import current_search, current_search_client

from ..utils import (
    get_entity_class,
    get_entity_indexer_class,
    get_entity_search_class,
    progressbar,
)
from .mef.api import ConceptMefRecord

RECORD_TYPES = ("cidref", "cognd", "corero")


def declared_association_fields(mapping_file):
    """Get the association fields a registered mapping file declares.

    :param mapping_file: Path of the mapping file.
    :returns: Field name -> mapping definition.
    """
    with open(mapping_file) as source:
        properties = json.load(source)["mappings"].get("properties", {})
    return {name: field for name, field in properties.items() if name.startswith("_association")}


def association_mapping_mismatches(record_types=RECORD_TYPES):
    """Get the association fields a live concept index does not map as declared.

    :param record_types: Record types to check.
    :returns: Generator of (index, field name, declared type, live type).
    """
    for record_type in record_types:
        alias = get_entity_search_class(record_type).Meta.index
        for index, mapping_file in current_search.aliases.get(alias, {}).items():
            if not current_search_client.indices.exists(index=index):
                continue
            mapping = current_search_client.indices.get_mapping(index=index)
            live = next(iter(mapping.values()))["mappings"].get("properties", {})
            for name, field in declared_association_fields(mapping_file).items():
                if live.get(name) != field:
                    yield index, name, field.get("type"), (live.get(name) or {}).get("type")


def assert_association_mappings(record_types=RECORD_TYPES):
    """Refuse to run while a concept index does not map the association fields.

    An index created before these fields existed maps them dynamically, and a dynamically mapped
    `_association_level` becomes a text field that the match level filter silently never matches.

    :param record_types: Record types to check.
    :raises RuntimeError: When a live index disagrees with its mapping file.
    """
    if not (mismatches := list(association_mapping_mismatches(record_types))):
        return
    for index, name, declared, live in mismatches:
        click.secho(f"  {index}: {name} is {live or 'missing'}, expected {declared}", fg="red")
    aliases = " -a ".join(get_entity_search_class(record_type).Meta.index for record_type in record_types)
    raise RuntimeError(f"Update the concept mappings first: invenio rero es index update-mapping -a {aliases}")


def pids_to_rebuild(pids, from_pid=None):
    """Get the pids left to rebuild, resuming at `from_pid`.

    `get_all_pids` orders by the persistent identifier id, so the pids a killed run had already committed are the ones
    before the one it stopped on and dropping them resumes it.

    :param pids: The pids of the record type, in the order they are rebuilt.
    :param from_pid: Pid to resume at, `None` to rebuild them all.
    :returns: The pids to rebuild.
    :raises click.BadParameter: When `from_pid` is not one of the pids.
    """
    if not from_pid:
        return pids
    if from_pid not in pids:
        raise click.BadParameter(f"{from_pid} is not one of the pids to rebuild")
    return pids[pids.index(from_pid) :]


def reindex_concepts(record_types=RECORD_TYPES):
    """Reindex every concept record, which is what fills the association fields.

    :param record_types: Record types to reindex.
    """
    for record_type in record_types:
        entity_class = get_entity_class(record_type)
        click.echo(f"  {record_type}: reindex {entity_class.count()} records")
        indexer = get_entity_indexer_class(record_type)()
        indexer.bulk_index(entity_class.get_all_ids())
        indexer.process_bulk_queue()
        entity_class.flush_indexes()


def rebuild_concept_mef(record_types=RECORD_TYPES, from_pid=None, verbose=True):
    """Rebuild the concept MEF records on the association identifier.

    Every record is committed on its own, so an interrupted run keeps what it did and the pid it stopped on is enough
    to resume it.

    :param record_types: Record types to rebuild.
    :param from_pid: Pid to resume the first record type at.
    :param verbose: Show a progress bar.
    """
    for record_type in record_types:
        entity_class = get_entity_class(record_type)
        entity_class.flush_indexes()
        pids = pids_to_rebuild(list(entity_class.get_all_pids()), from_pid)
        from_pid = None
        for pid in progressbar(items=pids, length=len(pids), label=record_type, verbose=verbose):
            try:
                if record := entity_class.get_record_by_pid(pid):
                    record.create_or_update_mef(dbcommit=True, reindex=True)
            except Exception:
                click.secho(
                    f"  {record_type} stopped on {pid}, resume with: invenio utils "
                    f"rebuild-concept-association -t {' -t '.join(record_types[record_types.index(record_type) :])} "
                    f"--no-reindex --from-pid {pid}",
                    fg="red",
                )
                raise
        ConceptMefRecord.flush_indexes()


def prune_orphan_mef(verbose=True):
    """Delete the concept MEF records the rebuild left without any entity.

    :param verbose: Show a progress bar.
    """
    orphan_pids = list(ConceptMefRecord.get_all_pids_without_entities_and_viaf())
    click.echo(f"  MEF records without any entity: {len(orphan_pids)}")
    for pid in progressbar(items=orphan_pids, length=len(orphan_pids), label="comef", verbose=verbose):
        if record := ConceptMefRecord.get_record_by_pid(pid):
            record.delete(force=True, dbcommit=True, delindex=True)
    ConceptMefRecord.flush_indexes()
