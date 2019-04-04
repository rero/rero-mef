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

from uuid import uuid4

from elasticsearch.exceptions import NotFoundError
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.api import Record

from .authorities.models import AgencyAction, MefAction


class AuthRecord(Record):
    """Authority Record class."""

    minter = None
    fetcher = None
    provider = None
    object_type = 'rec'
    agency = None
    agency_pid_type = None

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, **kwargs):
        """Create a new ils record."""
        assert cls.minter
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
    def create_or_update(
        cls,
        data,
        id_=None,
        delete_pid=True,
        dbcommit=False,
        reindex=False,
        **kwargs
    ):
        """Create or update agency record."""
        pid = data.get('pid')
        agency_record = cls.get_record_by_pid(pid)

        from .authorities.api import ViafRecord
        viaf_record = ViafRecord.get_viaf_by_agency_pid(
            pid, pid_type=cls.agency_pid_type
        )
        mef_action = agency_action = None
        return_record = {}
        if agency_record:
            if viaf_record:
                agency_record.update(data, dbcommit=dbcommit, reindex=reindex)
                mef_action = MefAction.UPDATE
                return_record = agency_record
                agency_action = AgencyAction.UPDATE
            else:
                mef_action = MefAction.DELETE
                agency_action = AgencyAction.DISCARD
        elif viaf_record:
            created_record = cls.create(
                data,
                id_=None,
                delete_pid=False,
                dbcommit=dbcommit,
                reindex=reindex,
            )
            mef_action = MefAction.UPDATE
            agency_action = AgencyAction.CREATE
            return_record = created_record
        else:
            mef_action = MefAction.DELETE
            agency_action = AgencyAction.DISCARD

        from .authorities.api import MefRecord
        MefRecord.create_or_update(
            agency=cls.agency,
            agency_pid=pid,
            viaf_record=viaf_record,
            action=mef_action,
            dbcommit=dbcommit,
            reindex=reindex,
        )
        return return_record, agency_action

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
    def get_all_pids(cls):
        """Get all records pids."""
        for persistent_identifier in PersistentIdentifier.query.filter_by(
                pid_type=cls.provider.pid_type):
            yield persistent_identifier.pid_value

    @classmethod
    def get_all_ids(cls):
        """Get all records uuids."""
        for persistent_identifier in PersistentIdentifier.query.filter_by(
                pid_type=cls.provider.pid_type):
            yield str(persistent_identifier.object_uuid)

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

    def delete(self, force=False, delindex=False):
        """Delete record and persistent identifier."""
        persistent_identifier = self.get_persistent_identifier(self.id)
        persistent_identifier.delete()
        result = super(AuthRecord, self).delete(force=force)
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

    def dbcommit(self, reindex=False, forceindex=False):
        """Commit changes to db."""
        db.session.commit()
        if reindex:
            self.reindex(forceindex=forceindex)

    def reindex(self, forceindex=False):
        """Reindex record."""
        if forceindex:
            RecordIndexer(version_type='external_gte').index(self)
        else:
            RecordIndexer().index(self)

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
