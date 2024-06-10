# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2022 RERO
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

"""Monitoring utilities."""


from datetime import datetime, timedelta, timezone

import click
from elasticsearch.exceptions import NotFoundError
from flask import current_app
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_search import RecordsSearch

from ..utils import get_entity_class, get_mefs_endpoints, progressbar


class Monitoring(object):
    """Monitoring class.

    The main idea here is to check the consistency between the database and
    the search index. We need to check that all documents presents in the
    database are also present in the search index and vice versa.
    """

    def __init__(self, time_delta=0):
        """Constructor.

        :param time_delta: Minutes tu substract from DB EScreation time.
        """
        self.time_delta = int(time_delta)

    def __str__(self):
        """Table representation of database and elasticsearch differences.

        :return: string representation of database and elasticsearch
        differences. Following columns are in the string:
            1. database count minus elasticsearch count
            2. document type
            3. database count
            4. elasticsearch index
            5. elasticsearch count
        """
        result = ""
        msg_head = f'DB - ES  {"type":>6} {"count":>10}'
        msg_head += f'  {"index":>25} {"count_es":>10}\n'
        msg_head += f'{"":-^64s}\n'

        for doc_type, info in sorted(self.info().items()):
            msg = (
                f'{info.get("db-es", ""):>7}  {doc_type:>6} '
                f'{info.get("db", ""):>10}'
            )
            if index := info.get("index", ""):
                msg += f'  {index:>25} {info.get("es", ""):>10}'
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
            date = datetime.now(timezone.utc)
            pids_es = {}
            query = RecordsSearch(index=index).filter("range", _created={"lte": date})
            progress = progressbar(
                items=query.source("pid").scan(), length=query.count(), verbose=verbose
            )
            for hit in progress:
                if pids_es.get(hit.pid):
                    pids_es_double.append(hit.pid)
                pids_es[hit.pid] = 1
            agent_class = get_entity_class(doc_type)
            pids_db = []
            progress = progressbar(
                items=agent_class.get_all_pids(
                    with_deleted=with_deleted,
                    date=date - timedelta(minutes=self.time_delta),
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
        :return: dictionair with database, elasticsearch and database minus
        elasticsearch count informations.
        """
        info = {}
        for doc_type, endpoint in current_app.config.get(
            "RECORDS_REST_ENDPOINTS"
        ).items():
            info[doc_type] = {}
            count_db = self.get_db_count(doc_type, with_deleted=with_deleted)
            info[doc_type]["db"] = count_db
            if index := endpoint.get("search_index", ""):
                count_es = self.get_es_count(index)
                db_es = count_db - count_es
                info[doc_type]["index"] = index
                info[doc_type]["es"] = count_es
                info[doc_type]["db-es"] = db_es
                if db_es == 0 and difference_db_es:
                    (
                        missing_in_db,
                        missing_in_es,
                        pids_es_double,
                        index,
                    ) = self.get_es_db_missing_pids(
                        doc_type=doc_type, with_deleted=with_deleted
                    )
                    if index:
                        if missing_in_db:
                            info[doc_type]["db-"] = list(missing_in_db)
                        if missing_in_es:
                            info[doc_type]["es-"] = list(missing_in_es)
        return info

    def check(self, with_deleted=False, difference_db_es=False):
        """Compaire elasticsearch with database counts.

        :param with_deleted: count also deleted items in database.
        :return: dictionair with all document types with a difference in
        database and elasticsearch counts.
        """
        checks = {}
        for info, data in self.info(
            with_deleted=with_deleted, difference_db_es=difference_db_es
        ).items():
            db_es = data.get("db-es", "")
            if db_es not in [0, ""]:
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
                mef_count = (
                    mef_search().filter("exists", field=entity_class.name).count()
                )
                db_count = entity_class.count()
                checks[entity] = {
                    "mef": mef_count,
                    "db": db_count,
                    "mef-db": mef_count - db_count,
                    "index": entity,
                }
        return checks

    def missing(self, doc_type, with_deleted=False):
        """Get missing pids.

        Get missing pids in database and elasticsearch and find duplicate
        pids in elasticsearch.

        :param doc_type: doc type to get missing pids.
        :return: dictionair with all missing pids.
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
        else:
            return {"ERROR": f"Document type not found: {doc_type}"}

    def print_missing(self, doc_type):
        """Print missing pids for the given document type.

        :param doc_type: doc type to print.
        """
        for info, data in self.missing(doc_type=doc_type).items():
            if info == "ERROR":
                click.secho(data, fg="red")
            elif data:
                if info == "ES duplicate":
                    click.secho(f"{doc_type}: duplicate in ES:", fg="red")
                    pid_counts = [f"{pid}: {count}" for pid, count in data.items()]
                    click.echo(", ".join(pid_counts))
                else:
                    click.secho(f"{doc_type}: pids missing in {info}:", fg="red")
                    click.echo(", ".join(data))
