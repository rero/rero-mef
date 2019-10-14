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

"""API for manipulating authorities."""

from invenio_search.api import RecordsSearch

from .fetchers import viaf_id_fetcher
from .minters import viaf_id_minter
from .models import ViafMetadata
from .providers import ViafProvider
from ..api import AuthRecord, AuthRecordIndexer
from ..models import AgencyAction


class ViafSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'viaf'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class ViafRecord(AuthRecord):
    """Viaf Authority class."""

    minter = viaf_id_minter
    fetcher = viaf_id_fetcher
    provider = ViafProvider
    model_cls = ViafMetadata

    @classmethod
    def get_viaf_by_agency_pid(cls, pid, pid_type):
        """Get viaf record by agency pid value."""
        search = ViafSearch()
        result = search.filter(
            'term', **{pid_type: pid}).source(includes=['pid']).scan()
        try:
            viaf_pid = next(result).pid
            return cls.get_record_by_pid(viaf_pid)
        except StopIteration:
            return None

    @classmethod
    def create_or_update(cls, data, id_=None, delete_pid=False, dbcommit=False,
                         reindex=False, **kwargs):
        """Create or update viaf record."""
        pid = data['pid']
        record = cls.get_record_by_pid(pid)
        if record:
            data['$schema'] = record['$schema']
            data['pid'] = record['pid']
            record.clear()
            record.update(data, dbcommit=dbcommit, reindex=reindex)
            return record, AgencyAction.UPDATE, None
        else:
            record = cls.create(data, dbcommit=dbcommit, reindex=reindex)
            return record, AgencyAction.CREATE, None


class ViafIndexer(AuthRecordIndexer):
    """ViafIndexer."""

    record_cls = ViafRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, op_type='index', doc_type='viaf')
