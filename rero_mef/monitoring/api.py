# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Monitoring of the MEF records, beside the shared monitoring of rero-invenio-base."""

from flask import current_app
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_search.engine import search
from rero_invenio_base.modules.monitoring import Monitoring as BaseMonitoring

from ..utils import get_entity_class, get_entity_search_class, get_mefs_endpoints


class Monitoring(BaseMonitoring):
    """Compare the database with the index, and check the MEF records and their sources."""

    @classmethod
    def get_dangling_pids(cls, doc_type):
        """Get the pids of a type that resolve to no record at all.

        A pid is minted before the record it names is validated, so a record refused by its schema used to leave the
        pid behind. Nothing answers to it and nothing can be created under it again. This finds those, telling them
        apart from the pids of a record that only got deleted, whose row is still there.

        Only a registered pid is one of those. A deleted one is the tombstone `get_all_deleted_pids` reads to tell
        the pid went, and taking it away would free the pid for another record.

        :param doc_type: Document type, the pid type of the entity.
        :returns: Sorted list of registered pid values naming no record row.
        """
        entity_class = get_entity_class(doc_type)
        if not entity_class:
            return []
        model_cls = entity_class.model_cls
        query = (
            PersistentIdentifier.query.outerjoin(model_cls, PersistentIdentifier.object_uuid == model_cls.id)
            .filter(PersistentIdentifier.pid_type == doc_type, PersistentIdentifier.status == PIDStatus.REGISTERED)
            .filter(model_cls.id.is_(None))
            .with_entities(PersistentIdentifier.pid_value)
        )
        return sorted(pid_value for (pid_value,) in query)

    @classmethod
    def get_dangling_redirects(cls, doc_type):
        """Get the `redirect_to` records of a type whose target no record holds.

        A GND record states in `relation_pid` where its pid went, and `EntityMefRecord.get_latest` reads that
        value to send a request for the old pid on to the new record. When nothing holds the target, the forward
        answers with nothing. The source normally delivers the target in the same harvest, so this is expected to
        find nothing.

        IdRef states the opposite relation, `redirect_from`, on the record that survived: there the value is the
        old pid, which is superseded and not expected to be held. Those are not reported.

        :param doc_type: Document type, the pid type of the entity.
        :returns: Sorted list of (pid, target pid) whose target is missing.
        """
        entity_class = get_entity_class(doc_type)
        search_class = get_entity_search_class(doc_type)
        if not entity_class or not search_class:
            return []
        redirects = [
            (hit.pid, hit.relation_pid.value)
            for hit in search_class()
            .filter("term", relation_pid__type="redirect_to")
            .source(["pid", "relation_pid"])
            .scan()
            if getattr(hit.relation_pid, "value", None)
        ]
        # One query per distinct target, not per redirect: several records can point at the same one. The record
        # row is required, not only the pid: a pid naming no record forwards to nothing, as a missing one does.
        model_cls = entity_class.model_cls
        targets = {target for _, target in redirects}
        held = (
            {
                pid_value
                for (pid_value,) in PersistentIdentifier.query.join(
                    model_cls, PersistentIdentifier.object_uuid == model_cls.id
                )
                .filter(PersistentIdentifier.pid_type == doc_type, PersistentIdentifier.pid_value.in_(targets))
                .with_entities(PersistentIdentifier.pid_value)
            }
            if targets
            else set()
        )
        return sorted(redirect for redirect in redirects if redirect[1] not in held)

    @classmethod
    def remove_dangling_pids(cls, doc_type):
        """Remove the pids of a type that resolve to no record at all.

        :param doc_type: Document type, the pid type of the entity.
        :returns: Sorted list of the pid values that are gone.
        """
        if not (pid_values := cls.get_dangling_pids(doc_type)):
            return []
        removed = PersistentIdentifier.query.filter(
            PersistentIdentifier.pid_type == doc_type,
            PersistentIdentifier.status == PIDStatus.REGISTERED,
            PersistentIdentifier.pid_value.in_(pid_values),
        ).delete(synchronize_session=False)
        db.session.commit()
        if removed == len(pid_values):
            return pid_values
        # Nothing can delete more rows than the pids named, so a smaller count means another run took some of
        # them first. What this one removed is what stopped dangling, and the caller is told that, not the plan.
        current_app.logger.warning(f"DANGLING PIDS: {doc_type} found {len(pid_values)}, removed {removed}")
        return sorted(set(pid_values) - set(cls.get_dangling_pids(doc_type)))

    def check_mef(self):
        """Compaire MEF and entities counts.

        returns: MEF, entities and MEF-entities counts.
        """
        checks = {}
        for mef in get_mefs_endpoints():
            mef_search = mef["mef_class"].search
            for entity in mef["endpoints"]:
                entity_class = get_entity_class(entity)
                try:
                    mef_count = mef_search().filter("exists", field=entity_class.name).count()
                except search.NotFoundError:
                    mef_count = f"No >>{mef['mef_class'].search.Meta.index}<< in search"
                db_count = entity_class.count()
                checks[entity] = {
                    "mef": mef_count,
                    "db": db_count,
                    "mef-db": mef_count - db_count if isinstance(mef_count, int) and isinstance(db_count, int) else "",
                    "index": entity,
                }
        return checks
