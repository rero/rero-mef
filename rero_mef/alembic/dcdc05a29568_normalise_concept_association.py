# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Normalise the concept BNF association identifier.

Nothing in the database changes shape here: the association identifiers live in
the search index, so the concept records have to be reindexed before their MEF
records can be rebuilt on the normalised identifier.

That rebuild is not run here. It takes hours over hundreds of thousands of
records, and alembic opens a transaction on the migration connection before the
first revision runs and holds it until the last one returns. The rebuild itself
never touches that connection, so it sits idle in a transaction for the whole
run, long enough for a server side idle timeout or a connection proxy to close
it, and the rollback that follows throws away every record already committed.
This revision therefore only checks that the indexes are ready and leaves the
rebuild to `invenio utils rebuild-concept-association`, which commits each
record on its own and can be resumed.
"""

import json

import click
from invenio_search import current_search, current_search_client

# revision identifiers, used by Alembic.
revision = "dcdc05a29568"
down_revision = "d8536341fc5e"
branch_labels = ()
depends_on = None

#: The concept indexes this revision requires to map the association fields, and the prefix naming them. Stated
#: here rather than read from `rero_mef.concepts.rebuild`: a revision has to keep running as it was written,
#: whatever the application does to its helpers afterwards.
CONCEPT_ALIASES = ("concepts_idref", "concepts_gnd", "concepts_rero")
ASSOCIATION_PREFIX = "_association"


def association_mapping_mismatches():
    """Get the association fields a live concept index does not map as its mapping file declares.

    :returns: Generator of (index, field name, declared type, live type).
    """
    for alias in CONCEPT_ALIASES:
        for index, mapping_file in current_search.aliases.get(alias, {}).items():
            if not current_search_client.indices.exists(index=index):
                continue
            with open(mapping_file) as source:
                properties = json.load(source)["mappings"].get("properties", {})
            declared = {name: field for name, field in properties.items() if name.startswith(ASSOCIATION_PREFIX)}
            mapping = current_search_client.indices.get_mapping(index=index)
            live = next(iter(mapping.values()))["mappings"].get("properties", {})
            for name, field in declared.items():
                if live.get(name) != field:
                    yield index, name, field.get("type"), (live.get(name) or {}).get("type")


def upgrade():
    """Upgrade database.

    :raises RuntimeError: While a live concept index disagrees with its mapping file. A dynamically mapped
        `_association_level` becomes a text field the match level filter silently never matches, so the rebuild
        must not run before the mappings are updated.
    """
    if mismatches := list(association_mapping_mismatches()):
        for index, name, declared, live in mismatches:
            click.secho(f"  {index}: {name} is {live or 'missing'}, expected {declared}", fg="red")
        aliases = " -a ".join(CONCEPT_ALIASES)
        raise RuntimeError(f"Update the concept mappings first: invenio rero es index update-mapping -a {aliases}")
    click.secho(
        "Concept indexes are ready. Rebuild the MEF records now, this revision does not:\n"
        "  invenio utils rebuild-concept-association",
        fg="yellow",
    )


def downgrade():
    """Downgrade database.

    The clusters cannot be rebuilt on the previous identifier, which the code no
    longer computes, and the MEF records left without entity are gone. Rolling
    back means reindexing and rebuilding with that older code.
    """
    click.secho("Nothing to undo: rebuild the concept MEF records with the previous code instead.", fg="yellow")
