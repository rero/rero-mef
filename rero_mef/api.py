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

from copy import deepcopy
from enum import Enum
from uuid import uuid4

from celery import current_app as current_celery_app
from elasticsearch import VERSION as ES_VERSION
from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import bulk
from elasticsearch.helpers import expand_action as default_expand_action
from flask import current_app
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_indexer.utils import _es7_expand_action
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.api import Record
from invenio_records_rest.utils import obj_or_import_string
from kombu.compat import Consumer
from sqlalchemy import func, text
from sqlalchemy.exc import OperationalError, StatementError
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
    ALREADYDELETED = 'already deleted'
    DELETEAGENT = 'delete agent'
    VALIDATIONERROR = 'validation error'
    ERROR = 'error'


class ReroMefRecordError:
    """Base class for errors in the Record class."""

    class Deleted(Exception):
        """Record is deleted."""

    class NotDeleted(Exception):
        """Record is not deleted."""

    class PidMissing(Exception):
        """Record pid missing."""

    class PidChange(Exception):
        """Record pid change."""

    class PidAlradyUsed(Exception):
        """Record pid already used."""

    class PidDoesNotExist(Exception):
        """Pid does not exist."""

    class DataMissing(Exception):
        """Data missing in record."""


class ReroMefRecord(Record):
    """Entity Record class."""

    minter = None
    fetcher = None
    provider = None
    object_type = 'rec'
    name = None
    viaf_source_code = None
    viaf_pid_name = None
    type = None

    @classmethod
    def create(cls, data, id_=None, delete_pid=False, dbcommit=False,
               reindex=False, md5=False, **kwargs):
        """Create a new agent record."""
        assert cls.minter
        if '$schema' not in data:
            data = add_schema(data, cls.provider.pid_type)
        if delete_pid:
            data.pop('pid', None)
        if not id_:
            id_ = uuid4()
        cls.minter(id_, data)
        if md5:
            data = add_md5(data)
        record = super().create(
            data=data,
            id_=id_,
            **kwargs
        )
        if dbcommit:
            record.dbcommit(reindex)
        return record

    def update_test_md5(self, data, dbcommit=False, reindex=False):
        """Update existing record.

        :param data: Data to test MD5 changes.
        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :returns: Record.
        """
        data = deepcopy(data)
        data = add_md5(data)
        if data.get('md5', 'data') == self.get('md5', 'agent'):
            # record has no changes
            return self, Action.UPTODATE
        return_record = self.replace(
            data=data, dbcommit=dbcommit, reindex=reindex)
        return return_record, Action.UPDATE

    @classmethod
    def create_or_update(cls, data, id_=None, delete_pid=True, dbcommit=False,
                         reindex=False, test_md5=False):
        """Create or update agent record."""
        agent_action = None
        return_record = data

        pid = data.get('pid')
        if agent_record := cls.get_record_by_pid(pid):
            # record exist
            data = add_schema(data, agent_record.provider.pid_type)
            # save the records old data if the new one is empty
            copy_fields = ['pid', '$schema', 'identifier', 'identifiedBy',
                           'authorized_access_point', 'bf:Agent',
                           'relation_pid', 'deleted']
            original_data = {
                k: v for k, v in agent_record.items() if k in copy_fields}
            # dict merging, `original_data` values
            # will be override by `data` values
            data = {**original_data, **data}

            if test_md5:
                return_record, agent_action = agent_record.update_test_md5(
                    data=data,
                    dbcommit=dbcommit,
                    reindex=reindex
                )
            else:
                agent_action = Action.UPDATE
                return_record = agent_record.replace(
                    data=data,
                    dbcommit=dbcommit,
                    reindex=reindex
                )
        else:
            try:
                return_record = cls.create(
                    data=data,
                    id_=None,
                    delete_pid=False,
                    dbcommit=dbcommit,
                    reindex=reindex,
                )
                agent_action = Action.CREATE
            except Exception as err:
                current_app.logger.error(
                    f'ERROR create_or_update {cls.name} '
                    f'{data.get("pid")} {err}'
                )
                agent_action = Action.ERROR
        return return_record, agent_action

    @classmethod
    def get_record_by_pid(cls, pid, with_deleted=False):
        """Get ils record by pid value."""
        assert cls.provider
        get_record_error_count = 0
        get_record_ok = False
        while not get_record_ok and get_record_error_count < 5:
            try:
                persistent_identifier = PersistentIdentifier.get(
                    cls.provider.pid_type,
                    pid
                )
                get_record_ok = True
                return super().get_record(persistent_identifier.object_uuid,
                                          with_deleted=with_deleted)

            except PIDDoesNotExistError:
                return None
            except NoResultFound:
                return None
            except OperationalError:
                get_record_error_count += 1
                msg = (f'Get record OperationalError: '
                       f'{get_record_error_count} {pid}')
                current_app.logger.error(msg)
                db.session.rollback()

    @classmethod
    def get_pid_by_id(cls, id):
        """Get pid by uuid."""
        persistent_identifier = cls.get_persistent_identifier(id)
        return str(persistent_identifier.pid_value)

    @classmethod
    def get_record_by_id(cls, id, with_deleted=False):
        """Get record by uuid."""
        return super().get_record(
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
        query = PersistentIdentifier \
            .query \
            .filter_by(pid_type=cls.provider.pid_type)
        if not with_deleted:
            query = query.filter_by(status=PIDStatus.REGISTERED)
        return query

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
    def get_all_deleted_pids(cls, limit=100000, from_date=None):
        """Get all records pids. Return a generator iterator."""
        query = PersistentIdentifier \
            .query \
            .filter_by(pid_type=cls.provider.pid_type) \
            .filter_by(status=PIDStatus.DELETED)
        if from_date:
            query = query \
                .filter(func.DATE(PersistentIdentifier.updated) >= from_date)
        if limit:
            # slower, less memory
            count = query.count()
            query = query.order_by(text('pid_value')).limit(limit)
            offset = 0
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
        get_count_ok = False
        get_count_count = 0
        while not get_count_ok and get_count_count < 5:
            try:
                get_count_ok = True
                return cls._get_all(with_deleted=with_deleted).count()
            except OperationalError:
                get_count_count += 1
                msg = f'Get count OperationalError: {get_count_count}'
                current_app.logger.error(msg)
                db.session.rollback()
        raise OperationalError('Get count')

    @classmethod
    def index_all(cls):
        """Index all records."""
        ids = cls.get_all_ids()
        return cls.index_ids(ids)

    @classmethod
    def index_ids(cls, ids):
        """Index ids."""
        count = 0
        for uuid in ids:
            count += 1
            RecordIndexer().index(cls.get_record_by_id(uuid))
        return count

    def delete(self, force=False, dbcommit=False, delindex=False):
        """Delete record and persistent identifier."""
        persistent_identifier = self.get_persistent_identifier(self.id)
        persistent_identifier.delete()
        result = super().delete(force=force)
        if dbcommit:
            self.dbcommit()
        if delindex:
            self.delete_from_index()
        return result, 'Deleted'

    def update(self, data, dbcommit=False, reindex=False):
        """Update data for record."""
        super().update(data)
        super().commit()
        if dbcommit:
            self.dbcommit(reindex)
        return self

    def replace(self, data, dbcommit=False, reindex=False):
        """Replace data in record."""
        new_data = deepcopy(data)
        pid = new_data.get('pid')
        if not pid:
            raise ReroMefRecordError.PidMissing(f'missing pid={self.pid}')
        self.clear()
        self = self.update(new_data, dbcommit=dbcommit, reindex=reindex)
        return self

    def dbcommit(self, reindex=False, forceindex=False):
        """Commit changes to db."""
        db.session.commit()
        if reindex:
            self.reindex(forceindex=forceindex)

    @classmethod
    def get_indexer_class(cls):
        """Get the indexer from config."""
        try:
            indexer = obj_or_import_string(
                current_app.config['RECORDS_REST_ENDPOINTS'][
                    cls.provider.pid_type
                ]['indexer_class']
            )
        except Exception:
            # provide default indexer if no indexer is defined in config.
            indexer = ReroIndexer
        return indexer

    def reindex(self, forceindex=False):
        """Reindex record."""
        indexer = self.get_indexer_class()
        if forceindex:
            return indexer(version_type='external_gte').index(self)
        return indexer().index(self)

    def delete_from_index(self):
        """Delete record from index."""
        indexer = self.get_indexer_class()
        try:
            indexer().delete(self)
        except NotFoundError:
            current_app.logger.warning(
                'Can not delete from index {class_name}: {pid}'.format(
                    class_name=self.__class__.__name__,
                    pid=self.pid
                )
            )

    @property
    def pid(self):
        """Get record pid value."""
        return self.get('pid')

    @property
    def persistent_identifier(self):
        """Get Persistent Identifier."""
        return self.get_persistent_identifier(self.id)

    @classmethod
    def get_metadata_identifier_names(cls):
        """Get metadata and identif table names."""
        metadata = cls.model_cls.__tablename__
        identifier = cls.provider.pid_identifier
        return metadata, identifier

    @property
    def deleted(self):
        """Get record deleted value."""
        return self.get('deleted')


class ReroIndexer(RecordIndexer):
    """Indexing class for mef."""

    index_error = {}

    def bulk_index(self, record_id_iterator, doc_type=None):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, op_type='index', doc_type=doc_type)

    def _get_indexer_class(self, payload):
        """Get the record class from payload."""
        # take the first defined doc type for finding the class
        pid_type = payload.get('doc_type', 'rec')
        try:
            indexer = obj_or_import_string(
                current_app.config[
                    'RECORDS_REST_ENDPOINTS'][pid_type]['indexer_class']
            )
        except Exception:
            # provide default indexer if no indexer is defined in config.
            indexer = ReroIndexer
        return indexer

    def process_bulk_queue(self, es_bulk_kwargs=None, stats_only=True):
        """Process bulk indexing queue.

        :param dict es_bulk_kwargs: Passed to
            :func:`elasticsearch:elasticsearch.helpers.bulk`.
        :param boolean stats_only: if `True` only report number of
            successful/failed operations instead of just number of
            successful and a list of error responses
        """
        with current_celery_app.pool.acquire(block=True) as conn:
            consumer = Consumer(
                connection=conn,
                queue=self.mq_queue.name,
                exchange=self.mq_exchange.name,
                routing_key=self.mq_routing_key,
            )

            req_timeout = current_app.config['INDEXER_BULK_REQUEST_TIMEOUT']

            es_bulk_kwargs = es_bulk_kwargs or {}
            count = bulk(
                self.client,
                self._actionsiter(consumer.iterqueue()),
                stats_only=stats_only,
                request_timeout=req_timeout,
                expand_action_callback=(
                    _es7_expand_action if ES_VERSION[0] >= 7
                    else default_expand_action
                ),
                **es_bulk_kwargs
            )

            consumer.close()

        return count

    def _actionsiter(self, message_iterator):
        """Iterate bulk actions.

        :param message_iterator: Iterator yielding messages from a queue.
        """
        for message in message_iterator:
            payload = message.decode()
            try:
                indexer_class = self._get_indexer_class(payload)
                if payload['op'] == 'delete':
                    yield indexer_class()._delete_action(payload=payload)
                else:
                    yield indexer_class()._index_action(payload=payload)
                message.ack()
            except NoResultFound:
                message.reject()
            except Exception:
                message.reject()
                uid = payload.get('id', '???')
                current_app.logger.error(
                    f"Failed to index record {uid}",
                    exc_info=True)

    def _index_action(self, payload):
        """Bulk index action.

        :param payload: Decoded message body.
        :returns: Dictionary defining an Elasticsearch bulk 'index' action.
        """
        get_record_error_count = 0
        get_record_ok = False
        while not get_record_ok and get_record_error_count < 5:
            try:
                record = self.record_cls.get_record(payload['id'])
                get_record_ok = True
            except StatementError:
                db.session.rollback()
                get_record_error_count += 1
                msg = ('INDEX ACTION StatementError: '
                       f'{get_record_error_count} {payload["id"]}')
                current_app.logger.error(msg)
            except OperationalError:
                get_record_error_count += 1
                msg = ('INDEX ACTION OperationalError: '
                       f'{get_record_error_count} {payload["id"]}')
                current_app.logger.error(msg)
                db.session.rollback()

        arguments = {}
        index, doc_type = self.record_to_index(record)

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
