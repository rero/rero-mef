# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2020 RERO
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
"""API for manipulating records."""

import click
from flask import current_app
from invenio_search import current_search

from ..api import Action, ReroIndexer, ReroMefRecord


class ConceptRecord(ReroMefRecord):
    """Concept record class."""

    name = None
    concept = None

    def __init__(self, *args, **kwargs):
        """Init class."""
        super().__init__(*args, **kwargs)
        self.concept = self.name

    @classmethod
    def update_indexes(cls):
        """Update indexes."""
        try:
            index = f'concepts_{cls.concept}'
            current_search.flush_and_refresh(index=index)
        except Exception as err:
            current_app.logger.error(f'ERROR flush and refresh: {err}')

    def delete_from_mef(self, dbcommit=False, reindex=False, verbose=False):
        """Delete concept from MEF record.

        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :param verbose: Verbose.
        :returns: MEF record, MEF action.
        """
        from .mef.api import ConceptMefRecord
        mef_action = Action.DISCARD
        old_mef_pid = 'None'
        mef_record = ConceptMefRecord.get_mef_by_entity_pid(
            self.pid, self.name)
        if mef_record:
            old_mef_pid = mef_record.pid
            if not mef_record.deleted:
                mef_record.pop(self.concept, None)
                mef_action = Action.DELETEAGENT
                mef_record = mef_record.replace(
                    data=mef_record, dbcommit=dbcommit, reindex=reindex)
                mef_record = ConceptMefRecord.create_deleted(
                    record=self, dbcommit=dbcommit, reindex=reindex)
            else:
                mef_action = Action.ALREADYDELETED
        else:
            # MEF record is missing create one
            mef_record = ConceptMefRecord.create_deleted(
                record=self, dbcommit=dbcommit, reindex=reindex)
            mef_action = Action.CREATE
        if reindex:
            ConceptMefRecord.update_indexes()
        if verbose:
            click.echo(
                f'Delete {self.concept}: {self.pid} '
                f'from mef: {old_mef_pid} {mef_action.value} '
                f'new mef: {mef_record.pid}'
            )
        return mef_record, mef_action

    def create_or_update_mef_viaf_record(self, dbcommit=False, reindex=False,
                                         online=False):
        """Create or update MEF and VIAF record.

        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :param online: Try to get VIAF record online.
        :returns: MEF record, MEF action, VIAF record, VIAF
        """
        viaf_record = None
        got_online = False
        # from .viaf.api import AgentViafRecord
        # AgentViafRecord.update_indexes()
        # viaf_record, got_online = AgentViafRecord.get_viaf_by_agent(
        #     concept=self,
        #     online=online
        # )
        from .mef.api import ConceptMefRecord
        ref_string = ConceptMefRecord.build_ref_string(
            concept=self.concept,
            concept_pid=self.pid
        )
        mef_data = {self.concept: {'$ref': ref_string}}
        mef_record = ConceptMefRecord.get_mef_by_entity_pid(
            self.pid, self.name)
        # if viaf_record:
        #     mef_data['viaf_pid'] = viaf_record.pid
        #     if not mef_record:
        #         mef_record = ConceptMefRecord.get_mef_by_viaf_pid(
        #             viaf_record.pid)
        if self.deleted:
            mef_record, mef_action = self.delete_from_mef(
                dbcommit=dbcommit,
                reindex=reindex
            )
        else:
            if mef_record:
                mef_action = Action.UPDATE
                mef_record = mef_record.update(
                    data=mef_data,
                    dbcommit=dbcommit,
                    reindex=reindex
                )
            else:
                mef_action = Action.CREATE
                mef_record = ConceptMefRecord.create(
                    data=mef_data,
                    dbcommit=dbcommit,
                    reindex=reindex,
                )
        if reindex:
            ConceptMefRecord.update_indexes()
        return mef_record, mef_action, viaf_record, got_online

    @property
    def deleted(self):
        """Get record deleted value."""
        return self.get('deleted')


class ConceptIndexer(ReroIndexer):
    """Indexing class for concepts."""
