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

"""API for manipulating contributions."""

from invenio_search.api import RecordsSearch

from .fetchers import rero_id_fetcher
from .minters import rero_id_minter
from .models import ReroMetadata
from .providers import ReroProvider
from ..api import AuthRecord, AuthRecordIndexer
from ..utils import add_md5


class ReroSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'rero'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class ReroRecord(AuthRecord):
    """Rero Authority class."""

    minter = rero_id_minter
    fetcher = rero_id_fetcher
    provider = ReroProvider
    agency = 'rero'
    viaf_source_code = 'RERO'
    agency_pid_type = 'rero_pid'
    model_cls = ReroMetadata

    @classmethod
    def create(cls, data, id_=None, delete_pid=False, dbcommit=False,
               reindex=False, **kwargs):
        """Create a new agency record."""
        data = add_md5(data)
        record = super(ReroRecord, cls).create(
            data=data,
            id_=id_,
            delete_pid=delete_pid,
            dbcommit=dbcommit,
            reindex=reindex,
            **kwargs
        )
        return record

    def update(self, data, dbcommit=False, reindex=False):
        """Update data for record."""
        data = add_md5(data)
        super(ReroRecord, self).update(data, dbcommit=dbcommit,
                                       reindex=reindex)
        return self

    @classmethod
    def get_online_record(cls, id, dbcommit=False, reindex=False,
                          test_md5=False, verbose=False):
        """Get online record."""
        from .tasks import rero_get_record
        return rero_get_record(id=id, dbcommit=dbcommit, reindex=reindex,
                               test_md5=test_md5, verbose=verbose)


class ReroIndexer(AuthRecordIndexer):
    """ReroIndexer."""

    record_cls = ReroRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, op_type='index', doc_type='rero')
