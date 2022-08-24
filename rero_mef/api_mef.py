# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2021 RERO
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

from datetime import datetime, timezone

import click
from elasticsearch_dsl import Q
from flask import current_app
from invenio_search import current_search

from .api import Action, ReroMefRecord
from .utils import get_entity_class, get_entity_classes, progressbar


class EntityMefRecord(ReroMefRecord):
    """Mef agent class."""

    minter = None
    fetcher = None
    provider = None
    model_cls = None
    viaf_cls = None
    search = None
    mef_type = ''

    @classmethod
    def get_mef_by_entity_pid(cls, entity_pid, entity_name, pid_only=False):
        """Get MEF record by entity pid value.

        :param entity_pid: Entety pid.
        :param entity_name: Name of entity (pid_type).
        :param pid_only: return pid only or the complete record.
        :returns: pid or record
        """
        key = f'{entity_name}.pid'
        search = cls.search() \
            .filter('term', **{key: entity_pid}) \
            .source(['pid'])
        if search.count() > 1:
            current_app.logger.error(
                f'MULTIPLE MEF FOUND FOR: {entity_name} {entity_pid}'
            )
        try:
            mef_pid = next(search.scan()).pid
            return mef_pid if pid_only else cls.get_record_by_pid(mef_pid)
        except StopIteration:
            return None

    @classmethod
    def get_mef_by_viaf_pid(cls, viaf_pid):
        """Get MEF record by agent pid value.

        :param viaf_pid: VIAF pid.
        :returns: Associated MEF record.
        """
        query = cls.search() \
            .filter('term', viaf_pid=viaf_pid)
        try:
            mef_pid = next(query.source(['pid']).scan()).pid
            return cls.get_record_by_pid(mef_pid)
        except StopIteration:
            return None

    @classmethod
    def get_all_pids_without_agents_and_viaf(cls):
        """Get all pids for records without agents and VIAF pids.

        :returns: Generator of MEF pids without agent links and without VIAF.
        """
        must_not = [Q('exists', field="viaf_pid")]
        must_not.extend(Q('exists', field=entity) for entity in cls.entities)
        query = cls.search().filter('bool', must_not=must_not)
        for hit in query.source('pid').scan():
            yield hit.pid

    @classmethod
    def get_all_pids_without_viaf(cls):
        """Get all pids for records without VIAF pid.

        :returns: Generator of MEF pids without VIAF pid.
        """
        query = cls.search() \
            .filter('bool', must_not=[Q('exists', field="viaf_pid")])
        for pid_type in current_app.config.get(cls.mef_type, []):
            query = query \
                .filter('bool', should=[Q('exists', field=pid_type)])
        for hit in query.source('pid').scan():
            yield hit.pid

    @classmethod
    def get_pids_with_multiple_mef(cls, record_types=[], verbose=False):
        """Get agent pids with multiple MEF records.

        :params record_types: Record types (pid_types).
        :param verbose: Verbose.
        :returns: pids, multiple pids, missing pids.
        """
        pids = {}
        multiple_pids = {}
        missing_pids = {}
        for record_type in record_types:
            if verbose:
                click.echo(f'Calculating {record_type}:')
            pids[record_type] = {}
            multiple_pids[record_type] = {}
            missing_pids[record_type] = []

            if agent_class := get_entity_class(record_type):
                agent_name = agent_class.name
                query = cls.search().filter('exists', field=agent_name)
                progress = progressbar(
                    items=query
                    .params(preserve_order=True)
                    .sort({'pid': {'order': 'asc'}})
                    .scan(),
                    length=query.count(),
                    verbose=verbose
                )
                for hit in progress:
                    data = hit.to_dict()
                    mef_pid = data['pid']
                    agent_pid = data[agent_name]['pid']
                    pids[record_type].setdefault(agent_pid, [])
                    pids[record_type][agent_pid].append(mef_pid)
                    if len(pids[record_type][agent_pid]) > 1:
                        multiple_pids[record_type][agent_pid] = \
                            pids[record_type][agent_pid]
                if len(pids[record_type]) < agent_class.count():
                    progress = progressbar(
                        items=agent_class.get_all_pids(),
                        length=agent_class.count(),
                        verbose=verbose
                    )
                    for pid in progress:
                        if not pids[record_type].pop(pid, None):
                            missing_pids[record_type].append(pid)
                else:
                    pids[record_type] = {}
            else:
                current_app.logger.error(
                    f'Record type not found: {record_type}')
        return pids, multiple_pids, missing_pids

    @classmethod
    def get_all_missing_pids(cls, record_types=None, verbose=False):
        """Get all missing agents.

        :params record_types: Record types (pid_type).
        :param verbose: Verbose.
        :returns: missing pids, to much pids.
        """
        if record_types is None:
            record_types = []
        missing_pids = {}
        to_much_pids = {}
        entity_classes = get_entity_classes()
        used_classes = {entity_class: entity_classes[entity_class]
                        for entity_class in entity_classes
                        if entity_class in record_types}

        for entity, entity_class in used_classes.items():
            if verbose:
                click.echo(f'Get pids from {entity} ...')
            missing_pids[entity] = {}
            progress = progressbar(
                items=entity_class.get_all_pids(),
                length=entity_class.count(),
                verbose=verbose
            )
            for pid in progress:
                missing_pids[entity][pid] = 1
        if verbose:
            click.echo('Get pids from MEF and calculate missing ...')
        progress = progressbar(
            items=cls.search().filter('match_all').scan(),
            length=cls.search().filter('match_all').count(),
            verbose=verbose
        )
        for hit in progress:
            pid = hit.pid

            data = hit.to_dict()
            for agent, agent_class in used_classes.items():
                if agent_data := data.get(agent_class.name):
                    agent_pid = agent_data.get('pid')
                    if not missing_pids[agent].pop(agent_pid, None):
                        to_much_pids.setdefault(pid, {})
                        to_much_pids[pid][agent] = agent_pid
        return missing_pids, to_much_pids

    def mark_as_deleted(self, dbcommit=False, reindex=False):
        """Mark record as deleted.

        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :returns: Modified record.
        """
        self['deleted'] = datetime.now(timezone.utc).isoformat()
        self.update(data=self, dbcommit=dbcommit, reindex=reindex)
        return self

    @classmethod
    def flush_indexes(cls):
        """Update indexes."""
        try:
            current_search.flush_and_refresh(index='mef')
        except Exception as err:
            current_app.logger.error(f'ERROR flush and refresh: {err}')

    def delete_ref(self, record, dbcommit=False, reindex=False):
        """Delete $ref from record.

        :param record: Record to delete the $ref.
        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :returns: Modified record and executed action.
        """
        action = Action.DISCARD
        if self.pop(record.name, None):
            action = Action.UPDATE
            self.replace(data=self, dbcommit=dbcommit, reindex=reindex)
            if reindex:
                self.flush_indexes()
        return self, action
