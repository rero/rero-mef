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
from time import sleep
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
from sqlalchemy import func
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import NoResultFound

from rero_mef.extensions import DeletedStateExtension, MD5Extension, SchemaExtension
from rero_mef.utils import build_ref_string, get_entity_class

_md5 = MD5Extension()

RERO_ILS_ENTITY_TYPES = {
    "bf:Person": "agents",
    "bf:Organisation": "agents",
    "bf:Topic": "concepts",
    "bf:Temporal": "concepts",
    "bf:Place": "places",
}


class Action(Enum):
    """Enumeration of all available entity record creation actions.

    This enum defines the possible outcomes when creating, updating, or deleting entity records in the system.
    """

    CREATE = "create"
    UPDATE = "update"
    REPLACE = "replace"
    UPTODATE = "uptodate"
    DISCARD = "discard"
    DELETE = "delete"
    ALREADY_DELETED = "already deleted"
    DELETE_ENTITY = "delete entity"
    VALIDATION_ERROR = "validation error"
    ERROR = "error"
    REDIRECT = "redirect"
    NOT_ONLINE = "not online"
    NOT_FOUND = "not found"


class EntityRecordError:
    """Base class for entity record errors.

    Contains all custom exception types raised during entity record operations such as creation, update, deletion, and
    PID management.
    """

    class Deleted(Exception):
        """Exception raised when attempting to access a deleted record."""

    class NotDeleted(Exception):
        """Exception raised when a record is expected to be deleted but is not."""

    class PidMissing(Exception):
        """Exception raised when a required PID (Persistent Identifier) is missing."""

    class PidChange(Exception):
        """Exception raised when attempting to change an immutable PID."""

    class PidAlreadyUsed(Exception):
        """Exception raised when attempting to use a PID that already exists."""

    class PidDoesNotExist(Exception):
        """Exception raised when a referenced PID cannot be found."""

    class DataMissing(Exception):
        """Exception raised when required data is missing from a record."""

    class DatabaseRetryError(Exception):
        """Exception raised when a database operation fails after all retries."""


class EntityRecord(Record):
    """Base class for entity records in the RERO MEF system.

    Provides common functionality for managing entity records including:
    - Creating, updating, and deleting records
    - Managing persistent identifiers (PIDs)
    - Indexing and searching
    - MD5 checksums for change detection
    - Database transaction management

    Subclasses should define:
    - minter: PID minter function
    - fetcher: PID fetcher function
    - provider: PID provider
    - name: Entity type name
    """

    minter = None
    fetcher = None
    provider = None
    object_type = "rec"
    name = None

    _extensions = [SchemaExtension(), DeletedStateExtension(), MD5Extension()]

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
        **kwargs,
    ):
        """Create a new entity record.

        :param data: Dictionary containing the record data.
        :param id_: UUID for the record. If None, a new UUID is generated.
        :param delete_pid: If True, remove 'pid' from data before creating.
        :param dbcommit: If True, commit changes to database and optionally reindex.
        :param reindex: If True and dbcommit is True, reindex the record.
        :param md5: If True, add MD5 checksum to the record data.
        :param kwargs: Additional arguments passed to parent create method.
        :returns: The newly created record instance.
        """
        assert cls.minter
        if delete_pid:
            data.pop("pid", None)
        if not id_:
            id_ = uuid4()
        cls.minter(id_, data)
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
        """Create a new record or update an existing one.

        Checks if a record with the given PID already exists. If it does, updates it; otherwise creates a new record.

        :param data: Dictionary containing the record data with 'pid' field.
        :param id_: UUID for the record (unused in this implementation).
        :param delete_pid: If True, remove 'pid' from data before creating.
        :param dbcommit: If True, commit changes to database.
        :param reindex: If True, reindex the record after changes.
        :param test_md5: If True, only update if MD5 checksum has changed.
        :returns: Tuple (record, action) where record is the EntityRecord instance
        and action is an Action enum value indicating what occurred.
        """
        action = Action.ERROR
        return_record = data

        pid = data.get("pid")
        if agent_record := cls.get_record_by_pid(pid):
            # Preserve critical fields from the existing record if they're missing in new data
            # to prevent accidental data loss during updates
            copy_fields = [
                "pid",
                "$schema",
                "identifiedBy",
                "authorized_access_point",
                "type",
                "relation_pid",
                "deleted",
            ]
            original_data = {k: v for k, v in agent_record.items() if k in copy_fields}
            data = {**original_data, **data}
            if test_md5:
                incoming_md5 = _md5.create_md5(
                    {k: v for k, v in data.items() if k not in ("$schema", "md5")}
                )
                if incoming_md5 == agent_record.get("md5"):
                    return_record = agent_record
                    action = Action.UPTODATE
                    if reindex:
                        cls.flush_indexes()
                    return return_record, action

            return_record = agent_record.replace(
                data=data, dbcommit=dbcommit, reindex=reindex
            )
            action = Action.REPLACE
        else:
            try:
                return_record = cls.create(
                    data=data,
                    id_=None,
                    delete_pid=False,
                    dbcommit=dbcommit,
                    reindex=reindex,
                )
                action = Action.CREATE
            except Exception as err:
                current_app.logger.error(
                    f"ERROR create_or_update {cls.name} {data.get('pid')} {err}"
                )
                action = Action.ERROR
        if reindex:
            cls.flush_indexes()
        return return_record, action

    def delete(self, force=True, dbcommit=False, delindex=False):
        """Delete record and its persistent identifier.

        :param force: If True, permanently delete the PID from database.
        :param dbcommit: If True, commit the deletion to database.
        :param delindex: If True, remove the record from search index.
        :returns: The deleted record instance.
        """
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
        super().update(data)
        if commit or dbcommit:
            self.commit()
        if dbcommit:
            self.dbcommit(reindex)
        return self

    def replace(self, data, commit=False, dbcommit=False, reindex=False):
        """Replace all record data with new data.

        Clears the current record and updates it with entirely new data. The PID must be present in the new data and
        match the existing PID.

        :param data: Dictionary containing the complete new record data.
        :param commit: If True, commit to the record (deprecated, use dbcommit).
        :param dbcommit: If True, commit changes to database.
        :param reindex: If True, reindex the record after replacement.
        :returns: The updated record instance.
        :raises EntityRecordError.PidMissing: If 'pid' is not in the new data.
        """
        new_data = deepcopy(data)
        pid = new_data.get("pid")
        if not pid:
            raise EntityRecordError.PidMissing(f"missing pid={self.pid}")
        self.clear()
        return self.update(
            data=new_data, commit=commit, dbcommit=dbcommit, reindex=reindex
        )

    def dbcommit(self, reindex=False, forceindex=False):
        """Commit changes to the database.

        :param reindex: If True, reindex the record after committing.
        :param forceindex: If True, use external version type for indexing.
        """
        db.session.commit()
        if reindex:
            self.reindex(forceindex=forceindex)

    def reindex(self, forceindex=False):
        """Reindex the record in the search engine.

        :param forceindex: If True, use external_gte version type to force indexing.
        :returns: Result of the indexing operation.
        """
        indexer = self.get_indexer_class()
        if forceindex:
            return indexer(version_type="external_gte").index(self)
        return indexer().index(self)

    @classmethod
    def get_record_by_pid(cls, pid, with_deleted=False):
        """Retrieve a record by its persistent identifier.

        Includes retry logic to handle transient database errors.

        :param pid: The persistent identifier value.
        :param with_deleted: If True, include deleted records in search.
        :returns: The record instance if found, None otherwise.
        """
        assert cls.provider
        for attempt in range(5):
            try:
                persistent_identifier = PersistentIdentifier.get(
                    cls.provider.pid_type, pid
                )
                return super().get_record(
                    persistent_identifier.object_uuid, with_deleted=with_deleted
                )
            except PIDDoesNotExistError:
                return None
            except NoResultFound:
                return None
            except OperationalError:
                current_app.logger.exception(
                    f"Get record OperationalError: {attempt + 1} {pid}"
                )
                db.session.rollback()
                sleep(2**attempt)
        current_app.logger.error(f"Get record failed after 5 retries: {pid}")
        return None

    @classmethod
    def get_pid_by_id(cls, id_):
        """Get the PID value from a record UUID.

        :param id_: The UUID of the record.
        :returns: The PID value associated with the UUID.
        """
        persistent_identifier = cls.get_persistent_identifier(id_)
        return str(persistent_identifier.pid_value)

    @classmethod
    def get_persistent_identifier(cls, id_):
        """Get the PersistentIdentifier object for a record UUID.

        :param id_: The UUID of the record.
        :returns: The persistent identifier object.
        """
        return PersistentIdentifier.get_by_object(
            cls.provider.pid_type, cls.object_type, id_
        )

    @classmethod
    def _get_all(cls, with_deleted=False, date=None):
        """Build a query for all persistent identifiers.

        :param with_deleted: If True, include deleted records.
        :param date: If provided, only include records created before this date.
        :returns: SQLAlchemy query object for persistent identifiers.
        """
        query = PersistentIdentifier.query.filter_by(pid_type=cls.provider.pid_type)
        if not with_deleted:
            query = query.filter_by(status=PIDStatus.REGISTERED)
        if date:
            query = query.filter(PersistentIdentifier.created < date)
        return query

    @classmethod
    def get_all_pids(cls, with_deleted=False, batch_size=1000, date=None):
        """Generate all record PIDs in batches.

        :param with_deleted: If True, include deleted records.
        :param date: If provided, only include records created before this date.
        :yields: PID values one at a time.
        """
        query = cls._get_all(with_deleted=with_deleted, date=date)
        offset = 0
        while batch := query.limit(batch_size).offset(offset).all():
            for identifier in batch:
                yield identifier.pid_value
            offset += batch_size

    @classmethod
    def get_all_deleted_pids(cls, batch_size=1000, from_date=None):
        """Generate PIDs of all deleted records in batches.

        :param batch_size: Number of records to fetch per database query.
        :param from_date: If provided, only include records deleted on or after this date.
        :yields: PID values of deleted records one at a time.
        """
        query = PersistentIdentifier.query.filter_by(
            pid_type=cls.provider.pid_type
        ).filter_by(status=PIDStatus.DELETED)
        if from_date:
            query = query.filter(func.DATE(PersistentIdentifier.updated) >= from_date)
        offset = 0
        while batch := query.limit(batch_size).offset(offset).all():
            for identifier in batch:
                yield identifier.pid_value
            offset += batch_size

    @classmethod
    def get_all_ids(cls, with_deleted=False, batch_size=1000, date=None):
        """Generate all record UUIDs in batches.

        :param with_deleted: If True, include deleted records.
        :param batch_size: Number of records to fetch per database query.
        :param date: If provided, only include records created before this date.
        :yields: Record UUIDs one at a time.
        """
        query = cls._get_all(with_deleted=with_deleted, date=date)
        offset = 0
        while batch := query.limit(batch_size).offset(offset).all():
            for identifier in batch:
                yield identifier.object_uuid
            offset += batch_size

    @classmethod
    def get_all_records(cls, with_deleted=False, batch_size=1000):
        """Generate all record instances in batches.

        :param with_deleted: If True, include deleted records.
        :param batch_size: Number of records to fetch per database query.
        :yields: Record instances one at a time.
        """
        for id_ in cls.get_all_ids(with_deleted=with_deleted, batch_size=batch_size):
            yield cls.get_record(id_)

    @classmethod
    def count(cls, with_deleted=False):
        """Count total number of records.

        Includes retry logic to handle transient database errors.

        :param with_deleted: If True, include deleted records in count.
        :returns: Total number of records.
        :raises EntityRecordError.DatabaseRetryError: If database operation fails after retries.
        """
        # Retry up to 5 times to handle transient database connection issues
        for attempt in range(5):
            try:
                return cls._get_all(with_deleted=with_deleted).count()
            except OperationalError:
                current_app.logger.exception(
                    f"Get count OperationalError: {attempt + 1}"
                )
                db.session.rollback()
                sleep(2**attempt)
        raise EntityRecordError.DatabaseRetryError("Get count failed after 5 retries")

    @classmethod
    def index_all(cls):
        """Index all records in the search engine.

        :returns: Number of records indexed.
        """
        ids = cls.get_all_ids()
        return cls.index_ids(ids)

    @classmethod
    def index_ids(cls, ids):
        """Index records by their UUIDs.

        :param ids: Iterable of record UUIDs to index.
        :returns: Number of records indexed.
        """
        count = 0
        for uuid in ids:
            count += 1
            RecordIndexer().index(cls.get_record(uuid))
        return count

    @classmethod
    def get_indexer_class(cls):
        """Get the indexer class from configuration.

        Returns the configured indexer class for this record type, or EntityIndexer as default if not configured.

        :returns: The indexer class to use for this record type.
        """
        try:
            indexer = obj_or_import_string(
                current_app.config["RECORDS_REST_ENDPOINTS"][cls.provider.pid_type][
                    "indexer_class"
                ]
            )
        except Exception:
            # provide default indexer if no indexer is defined in config.
            indexer = EntityIndexer
            current_app.logger.error(f"Get indexer class {cls.__name__}")
        return indexer

    def delete_from_index(self):
        """Remove this record from the search engine index.

        Logs a warning if the record is not found in the index.
        """
        indexer = self.get_indexer_class()
        try:
            indexer().delete(self)
        except NotFoundError:
            current_app.logger.warning(
                f"Can not delete from index {self.__class__.__name__}: {self.pid}"
            )

    @property
    def pid(self):
        """Get the record's persistent identifier value.

        :returns: The PID value.
        """
        return self.get("pid")

    @property
    def persistent_identifier(self):
        """Get the record's PersistentIdentifier object.

        :returns: The persistent identifier object.
        """
        return self.get_persistent_identifier(self.id)

    @classmethod
    def get_metadata_identifier_names(cls):
        """Get database table names for metadata and identifiers.

        :returns: Tuple (metadata_table_name, identifier_table_name).
        """
        metadata = cls.model_cls.__tablename__
        identifier = cls.provider.pid_identifier
        return metadata, identifier

    @property
    def deleted(self):
        """Get the record's deletion status.

        :returns: Deletion timestamp if deleted, None otherwise.
        """
        return self.get("deleted")


class ConceptPlaceRecord(EntityRecord):
    """Base class for Concept and Place entity records.

    Extends EntityRecord with functionality for managing associations between concepts/places and their MEF aggregation
    records. Handles linking of related records through association identifiers.
    """

    def get_association_record(self, association_cls, association_search):
        """Get the associated record linked via association identifier.

        Searches for an associated record (concept or place) that shares the same association identifier. Validates
        uniqueness and logs errors if multiple records are found.

        :param association_cls: The class of the associated record type.
        :param association_search: The search class for finding associated records.
        :returns: The associated record if found and unique, None if not found or multiple found.
        """
        if association_identifier := self.association_identifier:
            # Test if my identifier is unique
            count = (
                self.search()
                .filter("term", _association_identifier=association_identifier)
                .count()
            )
            if count > 1:
                current_app.logger.error(
                    f"MULTIPLE IDENTIFIERS FOUND FOR: {self.name} {self.pid} "
                    f"| {association_identifier}"
                )
                return None
            # Get associated record
            query = association_search().filter(
                "term", _association_identifier=association_identifier
            )
            associated_count = query.count()
            if associated_count > 1:
                current_app.logger.error(
                    f"MULTIPLE ASSOCIATIONS IDENTIFIERS FOUND FOR: {self.name} {self.pid} "
                    f"| {association_identifier}"
                )
            elif associated_count == 1:
                hit = next(query.source("pid").scan())
                return association_cls.get_record_by_pid(hit.pid)
        return None

    @property
    def association_identifier(self):
        """Get the association identifier for this record.

        This property must be implemented by concept/place subclasses to define how they identify related records.

        :returns: The association identifier value.
        :raises NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError()

    def create_or_update_mef(self, dbcommit=False, reindex=False):
        """Create or update the MEF record for this concept/place.

        Handles the complex logic of MEF record management:
        - Creates new MEF record if none exists
        - Updates existing MEF record with new references
        - Manages associations between related records
        - Handles merging and splitting of MEF records

        :param dbcommit: If True, commit changes to database.
        :param reindex: If True, reindex affected records.
        :returns: Tuple (mef_record, actions_dict) where mef_record is the
        MEF record instance and actions_dict maps MEF PIDs to Action enum values indicating what occurred.
        """

        def mef_create(mef_cls, data, association_identifier, dbcommit, reindex):
            """Create MEF record."""
            mef_data = {
                data.name: {
                    "$ref": build_ref_string(
                        entity_type=RERO_ILS_ENTITY_TYPES[data["type"]],
                        entity_name=data.name,
                        entity_pid=data.pid,
                    )
                },
                "type": data["type"],
            }
            if deleted := data.get("deleted"):
                mef_data["deleted"] = deleted
            if association_record := association_identifier.get("record"):
                ref = build_ref_string(
                    entity_type=RERO_ILS_ENTITY_TYPES[association_record["type"]],
                    entity_name=association_record.name,
                    entity_pid=association_record.pid,
                )
                mef_data[association_record.name] = {"$ref": ref}

            mef_record = mef_cls.create(
                data=mef_data,
                dbcommit=dbcommit,
                reindex=reindex,
            )
            return mef_record, {mef_record.pid: Action.CREATE}

        def get_mef_record(mef_cls, name, pid):
            """Get MEF record."""
            mef_records = mef_cls.get_mef(entity_name=name, entity_pid=pid)
            if len(mef_records) > 1:
                mef_pids = [mef_record.pid for mef_record in mef_records]
                current_app.logger.error(
                    f"MULTIPLE MEF FOUND FOR: {name} {pid} | mef: {', '.join(mef_pids)}"
                )
            if len(mef_records) == 1:
                return mef_records[0]
            return None

        association_info = self.association_info
        # Get direct MEF record
        mef_record = get_mef_record(
            mef_cls=association_info["mef_cls"], name=self.name, pid=self.pid
        )
        # Get associated MEF record
        mef_associated_record = None
        if associated_record := association_info["record"]:
            # Get MEF record for the associated record.
            mef_associated_record = get_mef_record(
                mef_cls=association_info["mef_cls"],
                name=associated_record.name,
                pid=associated_record.pid,
            )
        new_mef_record = mef_record or mef_associated_record

        actions = {}
        if not mef_record and not mef_associated_record:
            mef_record, actions = mef_create(
                mef_cls=association_info["mef_cls"],
                data=self,
                association_identifier=association_info,
                dbcommit=dbcommit,
                reindex=reindex,
            )
        else:
            mef_pids = mef_record.ref_pids if mef_record else {}
            mef_association_pids = (
                mef_associated_record.ref_pids if mef_associated_record else {}
            )
            association_name = association_info["record_cls"].name
            mef_self_pid = mef_pids.get(self.name)
            mef_self_association_pid = mef_association_pids.get(self.name)
            mef_other_pid = mef_pids.get(association_name)
            mef_other_association_pid = mef_association_pids.get(association_name)

            # New ref
            if not new_mef_record.get(self.name):
                # Add new ref
                new_mef_record[self.name] = {
                    "$ref": build_ref_string(
                        entity_type=RERO_ILS_ENTITY_TYPES[self["type"]],
                        entity_name=self.name,
                        entity_pid=self.pid,
                    )
                }
            if (
                not bool(mef_self_association_pid)
                and not bool(mef_other_association_pid)
                and bool(mef_other_pid)
            ):
                # Delete associated ref from MEF and create a new one
                new_mef_record.pop(association_name)
                if association_record := association_info[
                    "record_cls"
                ].get_record_by_pid(mef_other_pid):
                    _, action = mef_create(
                        mef_cls=association_info["mef_cls"],
                        data=association_record,
                        association_identifier={},
                        dbcommit=dbcommit,
                        reindex=reindex,
                    )
                    actions |= action
            if (
                bool(mef_self_pid)
                and not bool(mef_self_association_pid)
                and not bool(mef_other_pid)
                and bool(mef_other_association_pid)
            ):
                # Complex MEF reassociation: when current entity is in one MEF record
                # but its association is in a different MEF record, we need to:
                # 1. Remove the association from its current MEF record
                # 2. Add it to the MEF record containing the current entity
                ref = mef_associated_record.pop(association_name)
                associated_mef_record = mef_associated_record.replace(
                    data=mef_associated_record, dbcommit=dbcommit, reindex=reindex
                )
                actions[associated_mef_record.pid] = Action.DELETE_ENTITY
                new_mef_record[association_name] = ref
            if (
                bool(mef_self_pid)
                and not bool(mef_self_association_pid)
                and bool(mef_other_pid)
                and bool(mef_other_association_pid)
            ):
                # Delete entity from new MEF and add it to old MEF
                ref = new_mef_record.pop(self.name)
                new_mef_record.replace(
                    data=new_mef_record, dbcommit=dbcommit, reindex=reindex
                )
                actions[new_mef_record.pid] = Action.DELETE_ENTITY
                mef_associated_record[self.name] = ref
                new_mef_record = mef_associated_record

            mef_record = new_mef_record.replace(
                data=new_mef_record, dbcommit=dbcommit, reindex=reindex
            )
            actions[mef_record.pid] = Action.REPLACE

        association_info["mef_cls"].flush_indexes()
        return mef_record, actions

    @classmethod
    def get_online_record(cls, id_, debug=False):
        """Fetch a record from the online source.

        This method must be implemented by concept/place subclasses to define how they retrieve records from external
        sources.

        :param id_: The identifier of the record to fetch.
        :param debug: If True, print debug information during fetch.
        :returns: The fetched record data, or None if not found.
        :raises NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError()


class EntityIndexer(RecordIndexer):
    """Custom indexer for MEF entity records.

    Extends Invenio's RecordIndexer with MEF-specific functionality for bulk indexing operations and message queue
    processing.
    """

    def bulk_index(self, record_id_iterator, index=None, doc_type=None):
        """Submit bulk index operations to the message queue.

        :param record_id_iterator: Iterator yielding record UUIDs to index.
        :param index: Optional search engine index name override.
        :param doc_type: Optional document type for cross-type indexing.
        """
        self._bulk_op(
            record_id_iterator, op_type="index", index=index, doc_type=doc_type
        )

    def process_bulk_queue(self, search_bulk_kwargs=None, stats_only=True):
        """Process and execute bulk indexing operations from the queue.

        Consumes messages from the indexing queue and performs bulk operations against the search engine.

        :param search_bulk_kwargs: Additional keyword arguments for search.helpers.bulk.
        :param stats_only: If True, return only success/failure counts instead of detailed error responses.
        :returns: Indexing statistics (success count, failure count) if stats_only is True, otherwise detailed results.
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
        """Generate bulk actions from message queue iterator.

        Processes messages from the queue, converting them into search engine bulk action dictionaries. Handles
        acknowledgment and rejection of messages based on processing success.

        :param message_iterator: Iterator yielding messages from the indexing queue.
        :yields: Search engine bulk action specifications.
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
        """Create a bulk index action from a message payload.

        Retrieves the record, prepares its data for indexing, and constructs the search engine action dictionary.

        :param payload: Decoded message body containing record ID and operation details.
        :returns: Search engine bulk 'index' action specification including
        _id, _index, _source, and version information.
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
        """Send bulk operation messages to the indexing queue.

        Publishes messages for each record to the message queue for asynchronous processing by workers.

        :param record_id_iterator: Iterator yielding record UUIDs.
        :param op_type: Type of operation ('index', 'create', 'delete', 'update').
        :param index: Optional search engine index name override.
        :param doc_type: Optional document type for the operation.
        """
        with self.create_producer() as producer:
            for rec in record_id_iterator:
                data = {
                    "id": str(rec),
                    "op": op_type,
                    "index": index,
                    "doc_type": doc_type,
                }
                producer.publish(
                    data,
                    declare=[self.mq_queue],
                    **self.mq_publish_kwargs,
                )
