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
from uuid import uuid4

from elasticsearch.exceptions import NotFoundError
from flask import current_app
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.api import Record
from invenio_records_rest.utils import obj_or_import_string
from sqlalchemy.orm.exc import NoResultFound

from .mef.models import MefAction
from .models import AgencyAction
from .utils import add_md5, add_schema


class AuthRecordIndexer(RecordIndexer):
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


class AuthRecord(Record):
    """Authority Record class."""

    minter = None
    fetcher = None
    provider = None
    object_type = 'rec'
    agency = None
    agency_pid_type = None

    @classmethod
    def create(cls, data, id_=None, delete_pid=False, dbcommit=False,
               reindex=False, **kwargs):
        """Create a new agency record."""
        assert cls.minter
        if '$schema' not in data:
            type = cls.provider.pid_type
            data = add_schema(data, type)

        if delete_pid and data.get('pid'):
            del(data['pid'])
        if not id_:
            id_ = uuid4()
        cls.minter(id_, data)
        record = super(AuthRecord, cls).create(data=data, id_=id_, **kwargs)
        if dbcommit:
            record.dbcommit(reindex)
        return record

    @classmethod
    def create_or_update(cls, data, id_=None, delete_pid=True, dbcommit=False,
                         reindex=False, test_md5=False, **kwargs):
        """Create or update agency record."""
        pid = data.get('pid')
        agency_record = cls.get_record_by_pid(pid)

        from .viaf.api import ViafRecord
        viaf_record = ViafRecord.get_viaf_by_agency_pid(
            pid, pid_type=cls.agency_pid_type
        )
        mef_action = agency_action = None
        return_record = data
        if agency_record:
            if viaf_record:
                data = add_md5(data)
                data_md5 = data.get('md5', 'data')
                agency_md5 = agency_record.get('md5', 'agency')
                if test_md5 and data_md5 == agency_md5:
                    return_record = agency_record
                    agency_action = AgencyAction.UPTODATE
                    mef_action = MefAction.UPTODATE
                else:
                    data = add_schema(data, cls.agency)
                    return_record = agency_record.update(
                        data, dbcommit=dbcommit, reindex=reindex)
                    mef_action = MefAction.UPDATE
                    agency_action = AgencyAction.UPDATE
            else:
                mef_action = MefAction.DELETE
                agency_action = AgencyAction.DISCARD
        elif viaf_record:
            data = add_md5(data)
            data = add_schema(data, cls.agency)
            return_record = cls.create(
                data,
                id_=None,
                delete_pid=False,
                dbcommit=dbcommit,
                reindex=reindex,
            )
            mef_action = MefAction.UPDATE
            agency_action = AgencyAction.CREATE
        else:
            mef_action = MefAction.DELETE
            agency_action = AgencyAction.DISCARD

        from .mef.api import MefRecord
        mef_record, mef_action, dummy = MefRecord.create_or_update(
            agency=cls.agency,
            agency_pid=pid,
            viaf_record=viaf_record,
            action=mef_action,
            dbcommit=dbcommit,
            reindex=reindex,
        )
        return return_record, agency_action, mef_action

    @classmethod
    def get_record_by_pid(cls, pid):
        """Get ils record by pid value."""
        assert cls.provider
        try:
            persistent_identifier = PersistentIdentifier.get(
                cls.provider.pid_type,
                pid
            )
            return super(AuthRecord, cls).get_record(
                persistent_identifier.object_uuid
            )
        except PIDDoesNotExistError:
            return None

    @classmethod
    def get_pid_by_id(cls, id):
        """Get pid by uuid."""
        persistent_identifier = cls.get_persistent_identifier(id)
        return str(persistent_identifier.pid_value)

    @classmethod
    def get_record_by_id(cls, id):
        """Get record by uuid."""
        return super(AuthRecord, cls).get_record(id)

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
    def get_all_pids(cls, with_deleted=False, limit=10000):
        """Get all records pids. Return a generator iterator."""
        query = cls._get_all(with_deleted=with_deleted)
        offset = 0
        count = cls.count(with_deleted=with_deleted)
        while offset < count:
            for identifier in query.limit(limit).offset(offset):
                yield identifier.pid_value
            offset += limit

    @classmethod
    def get_all_ids(cls, with_deleted=False, limit=10000):
        """Get all records uuids. Return a generator iterator."""
        query = cls._get_all(with_deleted=with_deleted)
        offset = 0
        count = cls.count(with_deleted=with_deleted)
        while offset < count:
            for identifier in query.limit(limit).offset(offset):
                yield identifier.object_uuid
            offset += limit

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
        result = super(AuthRecord, self).delete(force=force)
        if dbcommit:
            self.dbcommit()
        if delindex:
            self.delete_from_index()
        return result

    def update(self, data, dbcommit=False, reindex=False):
        """Update data for record."""
        super(AuthRecord, self).update(data)
        super(AuthRecord, self).commit()
        if dbcommit:
            self.dbcommit(reindex)
        return self

    def replace(self, data, dbcommit=False, reindex=False):
        """Replace data in record."""
        new_data = deepcopy(data)
        pid = new_data.get('pid')
        if not pid:
            raise RecordIndexer.PidMissing(
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

    def delete_from_index(self):
        """Delete record from index."""
        try:
            RecordIndexer().delete(self)
        except NotFoundError:
            pass

    @property
    def pid(self):
        """Get ils record pid value."""
        return self.get('pid')

    @property
    def persistent_identifier(self):
        """Get Persistent Identifier."""
        return self.get_persistent_identifier(self.id)
