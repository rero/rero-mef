# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Monitoring utilities."""

from datetime import UTC, datetime, timedelta

import click
from elasticsearch.exceptions import NotFoundError
from flask import current_app
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_search import RecordsSearch

from ..utils import get_entity_class, get_entity_search_class, get_mefs_endpoints, progressbar


class Monitoring:
    """Monitoring class.

    The main idea here is to check the consistency between the database and the search index. We need to check that all
    documents presents in the database are also present in the search index and vice versa.
    """

    def __init__(self, time_delta=0):
        """Initialize Monitoring instance.

        :param time_delta: Minutes to subtract from DB/ES creation time.
        """
        self.time_delta = int(time_delta)

    def __str__(self):
        """Table representation of database and elasticsearch differences.

        :return: string representation of database and elasticsearch
        differences. Following columns are in the string: 1. database count minus elasticsearch count 2. document type
        3. database count 4. elasticsearch index 5. elasticsearch count
        """
        result = ""
        msg_head = f"DB - ES  {'type':>6} {'count':>10}"
        msg_head += f"  {'index':>25} {'count_es':>10}\n"
        msg_head += f"{'':-^64s}\n"

        for doc_type, info in sorted(self.info().items()):
            db_es_display = info.get("db-es")
            db_es_str = "" if db_es_display is None else db_es_display
            msg = f"{db_es_str:>7}  {doc_type:>6} {info.get('db', ''):>10}"
            if index := info.get("index", ""):
                msg += f"  {index:>25} {info.get('es', ''):>10}"
            result += msg + "\n"
        return msg_head + result

    @classmethod
    def get_db_count(cls, doc_type, with_deleted=False):
        """Get database count.

        Get count of items in the database for the given document type.

        :param doc_type: document type.
        :param with_deleted: count also deleted items.
        :return: item count.
        """
        if not current_app.config.get("RECORDS_REST_ENDPOINTS").get(doc_type):
            return f"No >>{doc_type}<< in DB"
        query = PersistentIdentifier.query.filter_by(pid_type=doc_type)
        if not with_deleted:
            query = query.filter_by(status=PIDStatus.REGISTERED)
        return query.count()

    @classmethod
    def get_dangling_pids(cls, doc_type):
        """Get the pids of a type that resolve to no record at all.

        A pid is minted before the record it names is validated, so a record refused by its schema used to leave the
        pid behind. Nothing answers to it and nothing can be created under it again. This finds those, telling them
        apart from the pids of a record that only got deleted, whose row is still there.

        :param doc_type: Document type, the pid type of the entity.
        :returns: Sorted list of pid values naming no record row.
        """
        entity_class = get_entity_class(doc_type)
        if not entity_class:
            return []
        model_cls = entity_class.model_cls
        query = (
            PersistentIdentifier.query.outerjoin(model_cls, PersistentIdentifier.object_uuid == model_cls.id)
            .filter(PersistentIdentifier.pid_type == doc_type)
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
        # One query per distinct target, not per redirect: several records can point at the same one.
        targets = {target for _, target in redirects}
        held = (
            {
                pid_value
                for (pid_value,) in PersistentIdentifier.query.filter(
                    PersistentIdentifier.pid_type == doc_type, PersistentIdentifier.pid_value.in_(targets)
                ).with_entities(PersistentIdentifier.pid_value)
            }
            if targets
            else set()
        )
        return sorted(redirect for redirect in redirects if redirect[1] not in held)

    @classmethod
    def remove_dangling_pids(cls, doc_type):
        """Remove the pids of a type that resolve to no record at all.

        :param doc_type: Document type, the pid type of the entity.
        :returns: Sorted list of the removed pid values.
        """
        if pid_values := cls.get_dangling_pids(doc_type):
            PersistentIdentifier.query.filter(
                PersistentIdentifier.pid_type == doc_type, PersistentIdentifier.pid_value.in_(pid_values)
            ).delete(synchronize_session=False)
            db.session.commit()
        return pid_values

    @classmethod
    def get_es_count(cls, index):
        """Get elasticsearch count.

        Get count of items in elasticsearch for the given index.

        :param index: index.
        :return: items count.
        """
        try:
            result = RecordsSearch(index=index).query().count()
        except NotFoundError:
            result = f"No >>{index}<< in ES"
        return result

    def get_es_db_missing_pids(self, doc_type, with_deleted=False, verbose=False):
        """Get ES and DB counts."""
        endpoint = current_app.config.get("RECORDS_REST_ENDPOINTS").get(doc_type, {})
        index = endpoint.get("search_index")
        pids_es_double = []
        pids_es = []
        pids_db = []
        if index:
            date = datetime.now(UTC) - timedelta(minutes=self.time_delta)
            pids_es = {}
            query = RecordsSearch(index=index).filter("range", _created={"lte": date})
            progress = progressbar(items=query.source("pid").scan(), length=query.count(), verbose=verbose)
            for hit in progress:
                if pids_es.get(hit.pid):
                    pids_es_double.append(hit.pid)
                pids_es[hit.pid] = 1
            agent_class = get_entity_class(doc_type)
            pids_db = []
            progress = progressbar(
                items=agent_class.get_all_pids(
                    with_deleted=with_deleted,
                    date=date,
                ),
                length=agent_class.count(with_deleted=with_deleted),
                verbose=verbose,
            )
            for pid in progress:
                if pids_es.get(pid):
                    pids_es.pop(pid)
                else:
                    pids_db.append(pid)
            pids_es = list(pids_es)
        return pids_es, pids_db, pids_es_double, index

    def info(self, with_deleted=False, difference_db_es=False):
        """Info.

        Get count details for all records rest endpoints in JSON format.

        :param with_deleted: count also deleted items in database.
        :return: dictionary with database, elasticsearch and database minus elasticsearch count information.
        """
        info = {}
        for doc_type, endpoint in current_app.config.get("RECORDS_REST_ENDPOINTS").items():
            info[doc_type] = {}
            count_db = self.get_db_count(doc_type, with_deleted=with_deleted)
            info[doc_type]["db"] = count_db
            if index := endpoint.get("search_index", ""):
                count_es = self.get_es_count(index)
                db_es = count_db - count_es if isinstance(count_db, int) and isinstance(count_es, int) else None
                info[doc_type]["index"] = index
                info[doc_type]["es"] = count_es
                info[doc_type]["db-es"] = db_es
                if db_es == 0 and difference_db_es:
                    (
                        missing_in_db,
                        missing_in_es,
                        pids_es_double,
                        index,
                    ) = self.get_es_db_missing_pids(doc_type=doc_type, with_deleted=with_deleted)
                    if index:
                        if missing_in_db:
                            info[doc_type]["db-"] = list(missing_in_db)
                        if missing_in_es:
                            info[doc_type]["es-"] = list(missing_in_es)
        return info

    def check(self, with_deleted=False, difference_db_es=False):
        """Compaire elasticsearch with database counts.

        :param with_deleted: count also deleted items in database.
        :return: dictionary with all document types with a difference in database and elasticsearch counts.
        """
        checks = {}
        for info, data in self.info(with_deleted=with_deleted, difference_db_es=difference_db_es).items():
            db_es = data.get("db-es", "")
            if db_es is None:
                checks.setdefault(info, {})
                checks[info]["es_error"] = "unavailable"
            elif isinstance(db_es, (int, float)) and db_es != 0:
                checks.setdefault(info, {})
                checks[info]["db_es"] = db_es
            if data.get("db-"):
                checks.setdefault(info, {})
                checks[info]["db-"] = len(data.get("db-"))
            if data.get("es-"):
                checks.setdefault(info, {})
                checks[info]["es-"] = len(data.get("es-"))
        return checks

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
                except NotFoundError:
                    mef_count = f"No >>{mef['mef_class'].search.Meta.index}<< in ES"
                db_count = entity_class.count()
                checks[entity] = {
                    "mef": mef_count,
                    "db": db_count,
                    "mef-db": mef_count - db_count if isinstance(mef_count, int) and isinstance(db_count, int) else "",
                    "index": entity,
                }
        return checks

    def missing(self, doc_type, with_deleted=False):
        """Get missing pids.

        Get missing pids in database and elasticsearch and find duplicate pids in elasticsearch.

        :param doc_type: doc type to get missing pids.
        :return: dictionary with all missing pids.
        """
        (
            missing_in_db,
            missing_in_es,
            pids_es_double,
            index,
        ) = self.get_es_db_missing_pids(doc_type=doc_type, with_deleted=with_deleted)
        if index:
            return {
                "DB": list(missing_in_db),
                "ES": list(missing_in_es),
                "ES duplicate": pids_es_double,
            }
        return {"ERROR": f"Document type not found: {doc_type}"}

    def print_missing(self, doc_type):
        """Print missing pids for the given document type.

        :param doc_type: doc type to print.
        """
        missing = self.missing(doc_type=doc_type)
        if "ERROR" in missing:
            click.secho(f"Error: {missing['ERROR']}", fg="yellow")
        else:
            if missing.get("ES duplicate"):
                click.secho(
                    f"ES duplicate {doc_type}: {', '.join(missing['ES duplicate'])}",
                    fg="red",
                )
            if missing.get("ES"):
                click.secho(f"ES missing {doc_type}: {', '.join(missing['ES'])}", fg="red")
            if missing.get("DB"):
                click.secho(f"DB missing {doc_type}: {', '.join(missing['DB'])}", fg="red")
