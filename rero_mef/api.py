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
from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import bulk
from flask import current_app
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.api import Record
from invenio_records_rest.utils import obj_or_import_string
from invenio_search import current_search
from invenio_search.engine import search
from kombu.compat import Consumer
from sqlalchemy import func, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import NoResultFound

from rero_mef.utils import get_entity_class

from .utils import add_md5, add_schema


class Action(Enum):
    """Class holding all availabe agent record creation actions."""

    CREATE = "create"
    UPDATE = "update"
    REPLACE = "replace"
    UPTODATE = "uptodate"
    DISCARD = "discard"
    DELETE = "delete"
    ALREADY_DELETED = "already deleted"
    DELETE_AGENT = "delete agent"
    VALIDATION_ERROR = "validation error"
    ERROR = "error"
    NOT_ONLINE = "not online"
    NOT_FOUND = "not found"


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
    object_type = "rec"
    name = None

    @classmethod
    def flush_indexes(cls):
        """Update indexes."""
        try:
            current_search.flush_and_refresh(cls.search.Meta.index)
        except Exception as err:
            current_app.logger.error(f"ERROR flush and refresh: {err}")

    @classmethod
    def create(
        cls,
        data,
        id_=None,
        delete_pid=False,
        dbcommit=False,
        reindex=False,
        md5=False,
        **kwargs,
    ):
        """Create a new agent record."""
        assert cls.minter
        if "$schema" not in data:
            data = add_schema(data, cls.provider.pid_type)
        if delete_pid:
            data.pop("pid", None)
        if not id_:
            id_ = uuid4()
        cls.minter(id_, data)
        if md5:
            data = add_md5(data)
        record = super().create(data=data, id_=id_, **kwargs)
        if dbcommit:
            record.dbcommit(reindex)
        return record

    @classmethod
    def create_or_update(
        cls,
        data,
        id_=None,
        delete_pid=True,
        dbcommit=False,
        reindex=False,
        test_md5=False,
    ):
        """Create or update agent record."""
        agent_action = None
        return_record = data

        pid = data.get("pid")
        if agent_record := cls.get_record_by_pid(pid):
            # record exist
            data = add_schema(data, agent_record.provider.pid_type)
            # save the records old data if the new one is empty
            copy_fields = [
                "pid",
                "$schema",
                "identifier",
                "identifiedBy",
                "authorized_access_point",
                "type",
                "relation_pid",
                "deleted",
            ]
            original_data = {k: v for k, v in agent_record.items() if k in copy_fields}
            # dict merging, `original_data` values
            # will be override by `data` values
            data = {**original_data, **data}

            if test_md5:
                return_record, agent_action = agent_record.update_md5_changed(
                    data=data, dbcommit=dbcommit, reindex=reindex
                )
            else:
                return_record = agent_record.replace(
                    data=data, dbcommit=dbcommit, reindex=reindex
                )
                agent_action = Action.UPDATE
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
                    f"ERROR create_or_update {cls.name} " f'{data.get("pid")} {err}'
                )
                agent_action = Action.ERROR
        if reindex:
            cls.flush_indexes()
        return return_record, agent_action

    def delete(self, force=True, dbcommit=False, delindex=False):
        """Delete record and persistent identifier."""
        persistent_identifier = self.get_persistent_identifier(self.id)
        persistent_identifier.delete()
        if force:
            db.session.delete(persistent_identifier)
        result = super().delete(force=force)
        if dbcommit:
            self.dbcommit()
        if delindex:
            self.delete_from_index()
            self.flush_indexes()
        return result

    def update(self, data, commit=False, dbcommit=False, reindex=False):
        """Update data for record.

        :param data: a dict data to update the record.
        :param commit: if True push the db transaction.
        :param dbcommit: make the change effective in db.
        :param reindex: reindex the record.
        :returns: the modified record
        """
        if self.get("md5"):
            data = add_md5(data)
        super().update(data)
        if commit or dbcommit:
            self.commit()
        if dbcommit:
            self.dbcommit(reindex)
        return self

    def update_md5_changed(self, data, dbcommit=False, reindex=False):
        """Testing md5 for update existing record.

        :param data: Data to test MD5 changes.
        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :returns: Record.
        """
        data = deepcopy(data)
        data = add_md5(data)
        if data.get("md5", "data") == self.get("md5", "agent"):
            # record has no changes
            return self, Action.UPTODATE
        return_record = self.replace(data=data, dbcommit=dbcommit, reindex=reindex)
        return return_record, Action.UPDATE

    def replace(self, data, commit=False, dbcommit=False, reindex=False):
        """Replace data in record."""
        new_data = deepcopy(data)
        pid = new_data.get("pid")
        if not pid:
            raise ReroMefRecordError.PidMissing(f"missing pid={self.pid}")
        if self.get("md5"):
            new_data = add_md5(new_data)
        self.clear()
        return self.update(
            data=new_data, commit=commit, dbcommit=dbcommit, reindex=reindex
        )

    def dbcommit(self, reindex=False, forceindex=False):
        """Commit changes to db."""
        db.session.commit()
        if reindex:
            self.reindex(forceindex=forceindex)

    def reindex(self, forceindex=False):
        """Reindex record."""
        indexer = self.get_indexer_class()
        if forceindex:
            return indexer(version_type="external_gte").index(self)
        return indexer().index(self)

    @classmethod
    def get_record_by_pid(cls, pid, with_deleted=False):
        """Get ils record by pid value."""
        assert cls.provider
        get_record_error_count = 0
        get_record_ok = False
        while not get_record_ok and get_record_error_count < 5:
            try:
                persistent_identifier = PersistentIdentifier.get(
                    cls.provider.pid_type, pid
                )
                get_record_ok = True
                return super().get_record(
                    persistent_identifier.object_uuid, with_deleted=with_deleted
                )

            except PIDDoesNotExistError:
                return None
            except NoResultFound:
                return None
            except OperationalError:
                get_record_error_count += 1
                msg = f"Get record OperationalError: " f"{get_record_error_count} {pid}"
                current_app.logger.error(msg)
                db.session.rollback()

    @classmethod
    def get_pid_by_id(cls, id_):
        """Get pid by uuid."""
        persistent_identifier = cls.get_persistent_identifier(id_)
        return str(persistent_identifier.pid_value)

    @classmethod
    def get_persistent_identifier(cls, id_):
        """Get Persistent Identifier."""
        return PersistentIdentifier.get_by_object(
            cls.provider.pid_type, cls.object_type, id_
        )

    @classmethod
    def _get_all(cls, with_deleted=False, date=None):
        """Get all persistent identifier records."""
        query = PersistentIdentifier.query.filter_by(pid_type=cls.provider.pid_type)
        if not with_deleted:
            query = query.filter_by(status=PIDStatus.REGISTERED)
        if date:
            query = query.filter(PersistentIdentifier.created < date)
        return query

    @classmethod
    def get_all_pids(cls, with_deleted=False, limit=100000, date=None):
        """Get all records pids. Return a generator iterator."""
        query = cls._get_all(with_deleted=with_deleted, date=date)
        if limit:
            # slower, less memory
            query = query.order_by(text("pid_value")).limit(limit)
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
        query = PersistentIdentifier.query.filter_by(
            pid_type=cls.provider.pid_type
        ).filter_by(status=PIDStatus.DELETED)
        if from_date:
            query = query.filter(func.DATE(PersistentIdentifier.updated) >= from_date)
        if limit:
            # slower, less memory
            count = query.count()
            query = query.order_by(text("pid_value")).limit(limit)
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
    def get_all_ids(cls, with_deleted=False, limit=100000, date=None):
        """Get all records uuids. Return a generator iterator."""
        query = cls._get_all(with_deleted=with_deleted, date=date)
        if limit:
            # slower, less memory
            query = query.order_by(text("pid_value")).limit(limit)
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
        for id_ in cls.get_all_ids(with_deleted=with_deleted, limit=limit):
            yield cls.get_record(id_)

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
                msg = f"Get count OperationalError: {get_count_count}"
                current_app.logger.error(msg)
                db.session.rollback()
        raise OperationalError("Get count")

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
            RecordIndexer().index(cls.get_record(uuid))
        return count

    @classmethod
    def get_indexer_class(cls):
        """Get the indexer from config."""
        try:
            indexer = obj_or_import_string(
                current_app.config["RECORDS_REST_ENDPOINTS"][cls.provider.pid_type][
                    "indexer_class"
                ]
            )
        except Exception:
            # provide default indexer if no indexer is defined in config.
            indexer = ReroIndexer
            current_app.logger.error(f"Get indexer class {cls.__name__}")
        return indexer

    def delete_from_index(self):
        """Delete record from index."""
        indexer = self.get_indexer_class()
        try:
            indexer().delete(self)
        except NotFoundError:
            current_app.logger.warning(
                "Can not delete from index {class_name}: {pid}".format(
                    class_name=self.__class__.__name__, pid=self.pid
                )
            )

    @property
    def pid(self):
        """Get record pid value."""
        return self.get("pid")

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
        return self.get("deleted")


class ReroIndexer(RecordIndexer):
    """Indexing class for mef."""

    def bulk_index(self, record_id_iterator, index=None, doc_type=None):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(
            record_id_iterator, op_type="index", index=index, doc_type=doc_type
        )

    def process_bulk_queue(self, search_bulk_kwargs=None, stats_only=True):
        """Process bulk indexing queue.

        :param dict search_bulk_kwargs: Passed to `search.helpers.bulk`.
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

            req_timeout = current_app.config["INDEXER_BULK_REQUEST_TIMEOUT"]

            search_bulk_kwargs = search_bulk_kwargs or {}

            count = bulk(
                self.client,
                self._actionsiter(consumer.iterqueue()),
                stats_only=stats_only,
                request_timeout=req_timeout,
                expand_action_callback=search.helpers.expand_action,
                **search_bulk_kwargs,
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
                if payload["op"] == "delete":
                    yield self._delete_action(payload=payload)
                else:
                    yield self._index_action(payload=payload)
                message.ack()
            except NoResultFound:
                message.reject()
            except Exception:
                message.reject()
                uid = payload.get("id", "???")
                current_app.logger.error(f"Failed to index record {uid}", exc_info=True)

    def _index_action(self, payload):
        """Bulk index action.

        :param payload: Decoded message body.
        :returns: Dictionary defining the search engine bulk 'index' action.
        """
        if doc_type := payload.get("doc_type"):
            record = get_entity_class(doc_type).get_record(payload["id"])
        else:
            record = self.record_cls.get_record(payload["id"])
        index = self.record_to_index(record)

        arguments = {}
        body = self._prepare_record(record, index, arguments)
        index = self._prepare_index(index)

        action = {
            "_op_type": "index",
            "_index": index,
            "_id": str(record.id),
            "_version": record.revision_id,
            "_version_type": self._version_type,
            "_source": body,
        }
        action.update(arguments)

        return action

    def _bulk_op(self, record_id_iterator, op_type, index=None, doc_type=None):
        """Index record in the search engine asynchronously.

        :param record_id_iterator: Iterator that yields record UUIDs.
        :param op_type: Indexing operation (one of ``index``, ``create``,
            ``delete`` or ``update``).
        :param index: The search engine index. (Default: ``None``)
        """
        with self.create_producer() as producer:
            for rec in record_id_iterator:
                data = dict(id=str(rec), op=op_type, index=index, doc_type=doc_type)
                producer.publish(
                    data,
                    declare=[self.mq_queue],
                    **self.mq_publish_kwargs,
                )
