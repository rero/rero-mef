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

import click

from rero_mef.concepts.rebuild import assert_association_mappings

# revision identifiers, used by Alembic.
revision = "dcdc05a29568"
down_revision = "d8536341fc5e"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    assert_association_mappings()
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
