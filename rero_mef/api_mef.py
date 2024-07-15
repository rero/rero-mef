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

"""API for manipulating MEF records."""


from copy import deepcopy
from datetime import datetime, timezone

import click
from dateutil import parser
from elasticsearch_dsl import Q
from flask import current_app

from .api import Action, ReroMefRecord
from .utils import generate, get_entity_class, get_entity_search_class, progressbar


class EntityMefRecord(ReroMefRecord):
    """Mef agent class."""

    minter = None
    fetcher = None
    provider = None
    model_cls = None
    viaf_cls = None
    search = None
    mef_type = ""

    def set_deleted(self):
        """Set deleted.

        Sets MEF deleted value from sources.
        """
        changed = False
        source_data = deepcopy(self).replace_refs()
        if sources := source_data["sources"]:
            for source in sources:
                if deleted := self[source].get("deleted"):
                    self["deleted"] = deleted
                    changed = True
                    break
            if not changed and self.get("deleted"):
                # Delete old deleted data
                self.pop("deleted")
                changed = True
        return changed

    def update(self, data, commit=False, dbcommit=False, reindex=False):
        """Update data for record.

        :param data: a dict data to update the record.
        :param commit: if True push the db transaction.
        :param dbcommit: make the change effective in db.
        :param reindex: reindex the record.
        :returns: the modified record
        """
        self.set_deleted()
        return super().update(
            data=data, commit=commit, dbcommit=dbcommit, reindex=reindex
        )

    @classmethod
    def get_mef(cls, agent_pid, agent_name, pid_only=False):
        """Get MEF record by agent pid value.

        :param agent_pid: Agent pid.
        :param agent_name: Name of agent (pid_type).
        :param pid_only: return pid only or the complete record.
        :returns: pid or record
        """
        key = f"{agent_name}.pid"
        if agent_name == "viaf":
            key = "viaf_pid"
        query = (
            cls.search()
            .filter("term", **{key: agent_pid})
            .params(preserve_order=True)
            .sort({"_updated": {"order": "desc"}})
        )
        if pid_only:
            mef_records = [hit.pid for hit in (query.source(["pid"]).scan())]
        else:
            mef_records = [cls.get_record(hit.meta.id) for hit in query.scan()]
        if len(mef_records) > 1:
            mef_pids = mef_records if pid_only else [mef.pid for mef in mef_records]
            current_app.logger.error(
                f"MULTIPLE MEF FOUND FOR: {agent_name} {agent_pid} | "
                f'mef: {", ".join(mef_pids)}'
            )
        return mef_records

    @classmethod
    def get_all_pids_without_agents_and_viaf(cls):
        """Get all pids for records without agents and VIAF pids.

        :returns: Generator of MEF pids without agent links and without VIAF.
        """
        must_not = [Q("exists", field="viaf_pid")]
        must_not.extend(Q("exists", field=agent) for agent in cls.entities)
        query = cls.search().filter("bool", must_not=must_not)
        for hit in query.source("pid").scan():
            yield hit.pid

    @classmethod
    def get_all_pids_without_viaf(cls):
        """Get all pids for records without VIAF pid.

        :returns: Generator of MEF pids without VIAF pid.
        """
        query = cls.search().exclude("exists", field="viaf_pid")
        for pid_type in current_app.config.get(cls.mef_type, []):
            query = query.filter("bool", should=[Q("exists", field=pid_type)])
        for hit in query.source("pid").scan():
            yield hit.pid

    @classmethod
    def get_multiple_missing_pids(cls, record_types=None, verbose=False):
        """Get agent pids with multiple MEF records.

        :params record_types: Record types (pid_types).
        :param verbose: Verbose.
        :param before: Get multiple MEF before x minutes (default 1 minute).
        :returns: pids, multiple pids, missing pids.
        """
        pids = {}
        multiple_pids = {}
        missing_pids = {}
        none_pids = {}
        agents = {}
        sources = ["pid"]
        for record_type in record_types or []:
            try:
                agent_class = get_entity_class(record_type)
                agents[record_type] = {
                    "name": agent_class.name,
                    "search": get_entity_search_class(record_type)(),
                }
                pids[record_type] = {}
                multiple_pids[record_type] = {}
                missing_pids[record_type] = []
                none_pids[record_type] = []
                sources.append(f"{agent_class.name}.pid")
            except Exception:
                current_app.logger.error(f"Record type not found: {record_type}")

        # Get all pids from MEF
        date = datetime.now(timezone.utc)
        click.echo("Get mef")
        progress = progressbar(
            items=cls.search()
            .params(preserve_order=True)
            .sort({"_updated": {"order": "desc"}})
            .source(sources)
            .scan(),
            length=cls.search().count(),
            verbose=verbose,
        )
        for hit in progress:
            data = hit.to_dict()
            mef_pid = data["pid"]
            for record_type, info in agents.items():
                if agent_data := data.get(info["name"]):
                    if agent_pid := agent_data.get("pid"):
                        pids[record_type].setdefault(agent_pid, []).append(mef_pid)
                        if len(pids[record_type][agent_pid]) > 1:
                            multiple_pids[record_type][agent_pid] = pids[record_type][
                                agent_pid
                            ]
                    else:
                        none_pids[record_type].append(mef_pid)
        # Get all agents pids and compare with MEF pids
        for record_type, info in agents.items():
            click.echo(f'Get {info["name"]} ' f"MEF: {len(pids[record_type])}")
            progress = progressbar(
                items=info["search"]
                .params(preserve_order=True)
                .sort({"pid": {"order": "asc"}})
                .filter("range", _created={"lte": date})
                .source("pid")
                .scan(),
                length=info["search"].filter("range", _created={"lte": date}).count(),
                verbose=verbose,
            )
            for hit in progress:
                pid = hit.pid
                if not pids[record_type].pop(pid, None):
                    missing_pids[record_type].append(pid)
        return pids, multiple_pids, missing_pids, none_pids

    @classmethod
    def get_deleted(cls, missing_pids, from_date):
        """Get deleted records."""
        # find deleted pids.
        for missing_pid in missing_pids:
            missing = {"pid": missing_pid}
            mef = cls.get_record_by_pid(missing_pid, with_deleted=True)
            if mef is None:
                yield missing
            elif mef == {}:
                # MEF was deleted!
                missing["_created"] = mef.created.isoformat()
                missing["_updated"] = mef.updated.isoformat()
                if from_date:
                    if mef.updated >= parser.isoparse(from_date):
                        yield missing
                else:
                    yield missing

    @classmethod
    def get_updated(cls, data):
        """Get latest Mef record for pid_type and pid.

        :param pid_type: pid type to use.
        :param pid: pid to use..
        :returns: latest record.
        """
        search = (
            cls.search().params(preserve_order=True).sort({"pid": {"order": "asc"}})
        )
        deleted = []
        from_date = data.get("from_date")
        if from_date:
            search = search.filter("range", _updated={"gte": from_date})
        missing_pids = []
        if pids := data.get("pids"):
            search = search.filter("terms", pid=pids)
            missing_pids.extend(
                pid for pid in pids if cls.search().filter("term", pid=pid).count() == 0
            )
        else:
            # Get all deleted pids.
            try:
                missing_pids = cls.get_all_deleted_pids(from_date=data.get("from_date"))
            except Exception as err:
                raise Exception(err)

        if not data.get("resolve"):
            search = search.source(["pid", "deleted", "_created", "_updated"])
        deleted = cls.get_deleted(missing_pids, from_date)
        return generate(search, deleted)

    def delete_ref(self, record, dbcommit=False, reindex=False):
        """Delete $ref from record.

        :param record: Record to delete the $ref.
        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :returns: Modified record and executed action.
        """
        action = Action.DISCARD
        if self.pop(record.name, None):
            action = Action.DELETE
            self.replace(data=self, dbcommit=dbcommit, reindex=reindex)
            if reindex:
                self.flush_indexes()
        return self, action

    def get_agents_pids(self):
        """Get agents pids."""
        agents = []
        agent_types = current_app.config.get(f"RERO_{self.mef_type}", [])
        for agent_type in agent_types:
            record_class = get_entity_class(agent_type)
            name = record_class.name
            if name in self:
                agents.append(
                    {
                        "record_class": record_class,
                        # Get pid from $ref URL
                        "pid": self.get(name).get("$ref").split("/")[-1],
                    }
                )
        return agents

    def get_agents_records(self):
        """Get agents records."""
        agents_records = []
        for agent in self.get_agents_pids():
            record_class = agent["record_class"]
            if agent_record := record_class.get_record_by_pid(agent["pid"]):
                agents_records.append(agent_record)
        return agents_records
