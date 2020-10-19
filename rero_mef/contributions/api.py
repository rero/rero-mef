# -*- coding: utf-8 -*-
#
# This file is part of RERO MEF.
# Copyright (C) 2018 RERO.
#
# RERO MEF is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO MEF is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO MEF; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""API for manipulating records."""

from copy import deepcopy
from enum import Enum
from uuid import uuid4

from elasticsearch.exceptions import NotFoundError
from flask import current_app
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.api import Record
from invenio_records_rest.utils import obj_or_import_string
from invenio_search import current_search
from sqlalchemy import text
from sqlalchemy.orm.exc import NoResultFound

from .utils import add_md5, add_schema


class Action(Enum):
    """Class holding all availabe agent record creation actions."""

    CREATE = 'create'
    UPDATE = 'update'
    REPLACE = 'replace'
    UPTODATE = 'uptodate'
    DISCARD = 'discard'
    DELETE = 'delete'
    DELETEAGENT = 'delete agent'
    VALIDATIONERROR = 'validation error'
    ERROR = 'error'


class ContributionRecordError:
    """Base class for errors in the ContributionRecord class."""

    class Deleted(Exception):
        """ContributionRecord is deleted."""

    class NotDeleted(Exception):
        """ContributionRecord is not deleted."""

    class PidMissing(Exception):
        """ContributionRecord pid missing."""

    class PidChange(Exception):
        """ContributionRecord pid change."""

    class PidAlradyUsed(Exception):
        """ContributionRecord pid already used."""

    class PidDoesNotExist(Exception):
        """Pid does not exist."""

    class DataMissing(Exception):
        """Data missing in record."""


class ContributionRecord(Record):
    """Authority Record class."""

    minter = None
    fetcher = None
    provider = None
    object_type = 'rec'
    viaf_source_code = None
    agent = None
    agent_pid_type = None

    @classmethod
    def create(cls, data, id_=None, delete_pid=False, dbcommit=False,
               reindex=False, md5=False, **kwargs):
        """Create a new agent record."""
        assert cls.minter
        if '$schema' not in data:
            type = cls.provider.pid_type
            data = add_schema(data, type)
        if delete_pid:
            data.pop('pid', None)
        if not id_:
            id_ = uuid4()
        cls.minter(id_, data)
        if md5:
            data = add_md5(data)
        record = super(ContributionRecord, cls).create(
            data=data,
            id_=id_,
            **kwargs
        )
        if dbcommit:
            record.dbcommit(reindex)
        return record

    @classmethod
    def create_or_update(cls, data, id_=None, delete_pid=True, dbcommit=False,
                         reindex=False, test_md5=False, online=True):
        """Create or update agent record."""
        mef_action = agent_action = None
        return_record = data

        pid = data.get('pid')
        agent_record = cls.get_record_by_pid(pid)

        if agent_record:
            # record exist
            if test_md5:
                return_record, agent_action = agent_record.update_test_md5(
                    data=data,
                    dbcommit=dbcommit,
                    reindex=reindex
                )
            else:
                agent_action = Action.UPDATE
                return_record = agent_record.update(
                    data=data,
                    dbcommit=dbcommit,
                    reindex=reindex
                )
        else:
            return_record = cls.create(
                data=data,
                id_=None,
                delete_pid=False,
                dbcommit=dbcommit,
                reindex=reindex,
            )
            agent_action = Action.CREATE
        return return_record, agent_action

    @classmethod
    def get_record_by_pid(cls, pid, with_deleted=False):
        """Get record by pid value."""
        assert cls.provider
        try:
            persistent_identifier = PersistentIdentifier.get(
                cls.provider.pid_type,
                pid
            )
            record = super(ContributionRecord, cls).get_record(
                persistent_identifier.object_uuid,
                with_deleted=with_deleted
            )
            return record
        except PIDDoesNotExistError:
            return None
        except NoResultFound:
            return None

    @classmethod
    def get_pid_by_id(cls, id):
        """Get pid by uuid."""
        persistent_identifier = cls.get_persistent_identifier(id)
        return str(persistent_identifier.pid_value)

    @classmethod
    def get_record_by_id(cls, id, with_deleted=False):
        """Get record by uuid."""
        return super(ContributionRecord, cls).get_record(
            id,
            with_deleted=with_deleted
        )

    @classmethod
    def get_persistent_identifier(cls, id):
        """Get Persistent Identifier."""
        return PersistentIdentifier.get_by_object(
            cls.provider.pid_type,
            cls.object_type,
            id
        )

    @classmethod
    def _get_all(cls, with_deleted=False):
        """Get all persistent identifier records."""
        query = PersistentIdentifier.query.filter_by(
            pid_type=cls.provider.pid_type
        )
        if not with_deleted:
            query = query.filter_by(status=PIDStatus.REGISTERED)
        return query

    @classmethod
    def get_filtered_pids(cls, filter):
        """Get all persistent identifier records."""
        from .mef.api import MefRecord
        from .viaf.api import ViafRecord
        if cls == ViafRecord:
            search_class_string = "rero_mef.contributions.viaf.api:ViafSearch"
        elif cls == MefRecord:
            search_class_string = "rero_mef.contributions.mef.api:MefSearch"
        else:
            search_class_string = current_app.config.\
                get('RECORDS_REST_ENDPOINTS').\
                get(cls.agent).\
                get('search_class', None)
        search_class = obj_or_import_string(search_class_string)
        query = search_class().filter(filter).source('pid')
        for hit in query:
            yield hit.pid

    @classmethod
    def get_all_pids(cls, with_deleted=False, limit=100000):
        """Get all records pids. Return a generator iterator."""
        query = cls._get_all(with_deleted=with_deleted)
        if limit:
            # slower, less memory
            query = query.order_by(text('pid_value')).limit(limit)
            offset = 0
            count = cls.count(with_deleted=with_deleted)
            while offset < count:
                for identifier in query.offset(offset):
                    yield identifier.pid_value
                offset += limit
        else:
            # faster, more memory
            for identifier in query:
                yield identifier.pid_value

    @classmethod
    def get_all_ids(cls, with_deleted=False, limit=100000):
        """Get all records uuids. Return a generator iterator."""
        query = cls._get_all(with_deleted=with_deleted)
        if limit:
            # slower, less memory
            query = query.order_by(text('pid_value')).limit(limit)
            offset = 0
            count = cls.count(with_deleted=with_deleted)
            while offset < count:
                for identifier in query.limit(limit).offset(offset):
                    yield identifier.object_uuid
                offset += limit
        else:
            # faster, more memory
            for identifier in query:
                yield identifier.object_uuid

    @classmethod
    def get_all_records(cls, with_deleted=False, limit=100000):
        """Get all records. Return a generator iterator."""
        for id in cls.get_all_ids(with_deleted=with_deleted, limit=limit):
            yield cls.get_record_by_id(id)

    @classmethod
    def count(cls, with_deleted=False):
        """Get record count."""
        return cls._get_all(with_deleted=with_deleted).count()

    @classmethod
    def index_all(cls):
        """Index all records."""
        ids = cls.get_all_ids()
        cls.index_ids(ids)
        return len(ids)

    @classmethod
    def index_ids(cls, ids):
        """Index ids."""
        for uuid in ids:
            RecordIndexer().index(cls.get_record_by_id(uuid))

    def delete(self, force=False, dbcommit=False, delindex=False):
        """Delete record and persistent identifier."""
        persistent_identifier = self.get_persistent_identifier(self.id)
        persistent_identifier.delete()
        result = super(ContributionRecord, self).delete(force=force)
        if dbcommit:
            self.dbcommit()
        if delindex:
            self.delete_from_index()
        return result, 'Deleted'

    def update(self, data, dbcommit=False, reindex=False):
        """Update data for record."""
        super(ContributionRecord, self).update(data)
        super(ContributionRecord, self).commit()
        if dbcommit:
            self.dbcommit(reindex)
        return self

    def replace(self, data, dbcommit=False, reindex=False):
        """Replace data in record."""
        new_data = deepcopy(data)
        pid = new_data.get('pid')
        if not pid:
            raise ContributionRecordError.PidMissing(
                'missing pid={pid}'.format(pid=self.pid)
            )
        self.clear()
        self = self.update(new_data, dbcommit=dbcommit, reindex=reindex)
        return self

    def dbcommit(self, reindex=False, forceindex=False):
        """Commit changes to db."""
        db.session.commit()
        if reindex:
            self.reindex(forceindex=forceindex)

    def reindex(self, forceindex=False):
        """Reindex record."""
        if forceindex:
            result = RecordIndexer(version_type='external_gte').index(self)
        else:
            result = RecordIndexer().index(self)
        return result

    @classmethod
    def update_indexes(cls):
        """Update indexes."""
        index = '{agent}-{agent}-contribution-v0.0.1'.format(
            agent=cls.agent
        )
        try:
            current_search.flush_and_refresh(index=index)
        except Exception as err:
            current_app.logger.error('ERROR flush and refresh: {err}'.format(
                err=err
            ))

    def delete_from_index(self):
        """Delete record from index."""
        try:
            RecordIndexer().delete(self)
        except NotFoundError:
            pass

    @property
    def pid(self):
        """Get record pid value."""
        return self.get('pid')

    @property
    def persistent_identifier(self):
        """Get Persistent Identifier."""
        return self.get_persistent_identifier(self.id)


class ContributionIndexer(RecordIndexer):
    """Indexing class for mef."""

    def bulk_index(self, record_id_iterator, doc_type=None):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, op_type='index', doc_type=doc_type)

    def _get_indexer_class(self, payload):
        """Get the record class from payload."""
        # take the first defined doc type for finding the class
        pid_type = payload.get('doc_type', 'rec')
        record_class = obj_or_import_string(
            current_app.config.get('RECORDS_REST_ENDPOINTS').get(
                pid_type
            ).get('indexer_class', RecordIndexer)
        )
        return record_class

    def _actionsiter(self, message_iterator):
        """Iterate bulk actions.

        :param message_iterator: Iterator yielding messages from a queue.
        """
        for message in message_iterator:
            payload = message.decode()
            try:
                indexer_class = self._get_indexer_class(payload)
                if payload['op'] == 'delete':
                    yield indexer_class()._delete_action(
                        payload=payload
                    )
                else:
                    yield indexer_class()._index_action(
                        payload=payload
                    )
                message.ack()
            except NoResultFound:
                message.reject()
            except Exception:
                message.reject()
                current_app.logger.error(
                    "Failed to index record {0}".format(payload.get('id')),
                    exc_info=True)

    def _index_action(self, payload):
        """Bulk index action.

        :param payload: Decoded message body.
        :returns: Dictionary defining an Elasticsearch bulk 'index' action.
        """
        record = self.record_cls.get_record(payload['id'])
        index, doc_type = self.record_to_index(record)

        arguments = {}
        body = self._prepare_record(record, index, doc_type, arguments)
        action = {
            '_op_type': 'index',
            '_index': index,
            '_type': doc_type,
            '_id': str(record.id),
            '_version': record.revision_id,
            '_version_type': self._version_type,
            '_source': body
        }
        action.update(arguments)

        return action
