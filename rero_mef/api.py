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
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidstore.resolver import Resolver
from invenio_records.api import Record


class MefRecord(Record):
    """ILS Record class."""

    minter = None
    fetcher = None
    provider = None
    object_type = 'rec'

    @classmethod
    def create(cls, data, id_=None, delete_pid=True,
               dbcommit=False, reindex=False, **kwargs):
        """Create a new ils record."""
        assert cls.minter
        if delete_pid and data.get('pid'):
            del(data['pid'])
        if not id_:
            id_ = uuid4()
        cls.minter(id_, data)
        record = super(MefRecord, cls).create(data=data, id_=id_, **kwargs)
        if dbcommit:
            record.dbcommit(reindex)
        return record

    @classmethod
    def get_record_by_pid(cls, pid, with_deleted=False):
        """Get ils record by pid value."""
        assert cls.provider
        resolver = Resolver(pid_type=cls.provider.pid_type,
                            object_type=cls.object_type,
                            getter=cls.get_record)
        persistent_identifier, record = resolver.resolve(str(pid))
        return super(MefRecord, cls).get_record(
            persistent_identifier.object_uuid,
            with_deleted=with_deleted
        )

    @classmethod
    def get_pid_by_id(cls, id):
        """Get pid by uuid."""
        persistent_identifier = cls.get_persistent_identifier(id)
        return str(persistent_identifier.pid_value)

    @classmethod
    def get_record_by_id(cls, id, with_deleted=False):
        """Get ils record by uuid."""
        return super(MefRecord, cls).get_record(id, with_deleted=with_deleted)

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
        pids = [n.pid_value for n in PersistentIdentifier.query.filter_by(
            pid_type=cls.provider.pid_type
        )]
        return pids

    @classmethod
    def get_all_ids(cls):
        """Get all records uuids."""
        uuids = [n.object_uuid for n in PersistentIdentifier.query.filter_by(
            pid_type=cls.provider.pid_type
        )]
        return uuids

    def delete(self, force=False, delindex=False):
        """Delete record and persistent identifier."""
        persistent_identifier = self.get_persistent_identifier(self.id)
        persistent_identifier.delete()
        result = super(MefRecord, self).delete(force=force)
        if delindex:
            self.delete_from_index()
        return result

    def update(self, data, dbcommit=False, reindex=False):
        """Update data for record."""
        super(MefRecord, self).update(data)
        super(MefRecord, self).commit()
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
            RecordIndexer(version_type="external_gte").index(self)
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
