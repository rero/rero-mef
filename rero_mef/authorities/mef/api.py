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

from datetime import datetime

import click
import pytz
from elasticsearch_dsl import Q
from flask import current_app
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_rest.utils import obj_or_import_string
from invenio_search import current_search
from invenio_search.api import RecordsSearch

from .fetchers import mef_id_fetcher
from .minters import mef_id_minter
from .models import MefAction, MefMetadata
from .providers import MefProvider
from ..api import AuthRecord, AuthRecordIndexer
from ..utils import add_schema, get_agencies_endpoints, get_agency_classes, \
    progressbar


class MefSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'mef'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class MefRecord(AuthRecord):
    """Mef Authority class."""

    minter = mef_id_minter
    fetcher = mef_id_fetcher
    provider = MefProvider
    model_cls = MefMetadata

    @classmethod
    def build_ref_string(cls, agency_pid, agency):
        """Build url for agency's api."""
        with current_app.app_context():
            ref_string = '{url}/api/{agency}/{pid}'.format(
                url=current_app.config.get('RERO_MEF_APP_BASE_URL'),
                agency=agency,
                pid=agency_pid
            )
            return ref_string

    @classmethod
    def get_mef_by_agency_pid(cls, agency_pid, agency, pid_only=False):
        """Get mef record by agency pid value."""
        key = '{agency}.pid'.format(agency=agency)
        search = MefSearch()
        result = search.query(
            'match', **{key: agency_pid}).source(['pid']).scan()
        try:
            mef_pid = next(result).pid
            if pid_only:
                return mef_pid
            else:
                return cls.get_record_by_pid(mef_pid)
        except StopIteration:
            return None

    @classmethod
    def get_all_mef_pids_by_agency(cls, agency):
        """Get all mef pids for agency."""
        key = '{agency}{identifier}'.format(
            agency=agency, identifier='.pid')
        search = MefSearch()
        results = search.filter(
            'exists',
            field=key
        ).source(['pid', key]).scan()
        for result in results:
            result_dict = result.to_dict()
            yield result_dict.get(agency, {}).get('pid'),\
                result_dict.get('pid')

    @classmethod
    def get_mef_by_viaf_pid(cls, viaf_pid):
        """Get mef record by agency pid value."""
        search = MefSearch()
        result = search.filter(
            'term', viaf_pid=viaf_pid).source(['pid']).scan()
        try:
            mef_pid = next(result).pid
            return cls.get_record_by_pid(mef_pid)
        except StopIteration:
            return None

    @classmethod
    def mef_data_from_viaf(cls, mef_data, viaf_record):
        """Create Mef data from Viaf."""
        has_refs = False
        if not mef_data:
            mef_data = {}
        if viaf_record and viaf_record.get('pid'):
            mef_data['viaf_pid'] = viaf_record.get('pid')
        for agency, agency_data in get_agencies_endpoints().items():
            mef_data.pop(agency, None)
            pid_name = '{agency}_pid'.format(agency=agency)
            pid_value = viaf_record.get(pid_name)
            if pid_value:
                agency_class = obj_or_import_string(
                    agency_data.get('record_class')
                )
                try:
                    PersistentIdentifier.get(
                        agency_class.provider.pid_type,
                        pid_value
                    )
                    ref_string = cls.build_ref_string(
                        agency=agency, agency_pid=pid_value
                    )
                    mef_data[agency] = {'$ref': ref_string}
                    has_refs = True
                except PIDDoesNotExistError:
                    pass
        return mef_data, has_refs

    @classmethod
    def create_or_update(cls, viaf_record, action=None, agency=None,
                         agency_pid=None, delete_pid=True, dbcommit=False,
                         reindex=False, test_md5=False, **kwargs):
        """Create, update or delete Mef record."""
        record = None
        if action not in [MefAction.DISCARD, MefAction.UPTODATE]:
            if viaf_record:
                viaf_pid = viaf_record.get('pid')
                mef_record = cls.get_mef_by_viaf_pid(viaf_pid=viaf_pid)
            else:
                mef_record = cls.get_mef_by_agency_pid(
                    agency_pid=agency_pid, agency=agency
                )
                viaf_record = {
                    "{agency}_pid".format(agency=agency): agency_pid
                }
            mef_data, mef_has_refs = MefRecord.mef_data_from_viaf(
                mef_record, viaf_record)

            if not mef_has_refs:
                action = MefAction.DELETE
            if not mef_record:
                action = MefAction.CREATE

            if action == MefAction.CREATE:
                mef_data = add_schema(mef_data, 'mef')
                record = MefRecord.create(
                    data=mef_data,
                    id_=None,
                    delete_pid=True,
                    dbcommit=dbcommit,
                    reindex=reindex
                    )
            elif action in [MefAction.UPDATE, MefAction.REPLACE]:
                record = mef_record.replace(
                    data=mef_data,
                    dbcommit=dbcommit,
                    reindex=reindex
                )
            elif action == MefAction.DELETE:
                if mef_record:
                    mef_record.pop(agency, None)
                    if len(mef_record) > 2:
                        record = mef_record.update(
                            mef_record,
                            dbcommit=dbcommit,
                            reindex=reindex,
                        )
                    else:
                        mef_record.delete(dbcommit=True, delindex=True)
                        action = MefAction.DELETEMEF
            elif action == MefAction.UPTODATE:
                pass
            else:
                raise NotImplementedError
        return record, action, None

    @classmethod
    def update_indexes(cls):
        """Update indexes."""
        index = 'mef-mef-person-v0.0.1'
        current_search.flush_and_refresh(index=index)

    def create_mef(self, dbcommit=False, reindex=False, verbose=False):
        """Create MEF records."""
        return MefAction.DISCARD

    @classmethod
    def get_all_pids_without_agencies_viaf(cls):
        """Get all pids for records without agencies and viaf pids."""
        query = MefSearch()\
            .filter('bool', must_not=[Q('exists', field="viaf_pid")]) \
            .filter('bool', must_not=[Q('exists', field="bnf")]) \
            .filter('bool', must_not=[Q('exists', field="gnd")]) \
            .filter('bool', must_not=[Q('exists', field="idref")]) \
            .filter('bool', must_not=[Q('exists', field="rero")]) \
            .source('pid')\
            .scan()
        for hit in query:
            yield hit.pid

    @classmethod
    def get_all_pids_without_viaf(cls):
        """Get all pids for records without viaf pid."""
        query = MefSearch()\
            .filter('bool', must_not=[Q('exists', field="viaf_pid")])\
            .filter('bool', should=[Q('exists', field="bnf")]) \
            .filter('bool', should=[Q('exists', field="gnd")]) \
            .filter('bool', should=[Q('exists', field="idref")]) \
            .filter('bool', should=[Q('exists', field="rero")]) \
            .source('pid')\
            .scan()
        for hit in query:
            yield hit.pid

    @classmethod
    def get_all_missing_agencies_pids(
            cls,
            agencies=['bnf', 'gnd', 'idref', 'rero'],
            verbose=False
    ):
        """Get all missing agencies."""
        missing_pids = {}
        agency_classes = get_agency_classes()
        for agency, agency_class in agency_classes.items():
            if agency in agencies:
                if verbose:
                    click.echo(
                        'Get pids from {agency} ...'.format(agency=agency)
                    )
                missing_pids[agency] = {}
                progress = progressbar(
                    items=agency_class.get_all_pids(),
                    length=agency_class.count(),
                    verbose=verbose
                )
                for pid in progress:
                    missing_pids[agency][pid] = 1
        if verbose:
            click.echo('Get pids from mef and calculate missing ...')
        progress = progressbar(
            items=cls.get_all_ids(),
            length=cls.count(),
            verbose=verbose
        )
        for id in progress:
            mef_record = cls.get_record_by_id(id)
            for agency in agency_classes:
                if agency in agencies:
                    agency_ref = mef_record.get(agency, {}).get('$ref', '')
                    agency_pid = agency_ref.split('/')[-1]
                    missing_pids[agency].pop(agency_pid, None)
        return missing_pids

    def mark_as_deleted(self, dbcommit=False, reindex=False):
        """Mark record as deleted."""
        # if current_app.config['INDEXER_REPLACE_REFS']:
        #     data = deepcopy(self.replace_refs())
        # else:
        #     data = self.dumps()
        # data['_deleted'] = pytz.utc.localize(self.created).isoformat()
        #
        # indexer = MefIndexer()
        # index, doc_type = indexer.record_to_index(self)
        # print('---->', index, doc_type)
        # body = indexer._prepare_record(data, index, doc_type)
        # index, doc_type = indexer._prepare_index(index, doc_type)
        # print('---->', index, doc_type)
        #
        # return indexer.client.index(
        #     id=str(self.id),
        #     version=self.revision_id,
        #     version_type=indexer._version_type,
        #     index=index,
        #     doc_type=doc_type,
        #     body=body
        # )
        self['deleted'] = pytz.utc.localize(datetime.now()).isoformat()
        self.update(data=self, dbcommit=dbcommit, reindex=reindex)
        return self

    def create_or_update_mef_viaf_record(self, dbcommit=False, reindex=False,
                                         online=True):
        """Create or update MEF and VIAF record."""
        from ..viaf.api import ViafRecord
        actions = {}
        agency_classes = get_agency_classes()
        for agency, agency_class in agency_classes.items():
            if self.get(agency):
                agency_ref = self.get(agency, {}).get('$ref')
                agency_pid = agency_ref.split('/')[-1]
                agency_record = agency_class.get_record_by_pid(agency_pid)
                mef_record, mef_action, has_viaf = \
                    agency_record.create_or_update_mef_viaf_record(
                        dbcommit=dbcommit,
                        reindex=reindex,
                        online=online
                    )
                MefRecord.update_indexes()
                ViafRecord.update_indexes()
                actions[agency] = (mef_record.get('pid'), mef_action, has_viaf)
                if mef_record.get('pid') and mef_record.get('pid') != self.pid:
                    self.pop(agency)
        if len(self) > 2:
            record = self.replace(
                data=self,
                dbcommit=dbcommit,
                reindex=reindex,
            )
        else:
            record = self.mark_as_deleted(dbcommit=True, reindex=True)
        return record, actions


class MefIndexer(AuthRecordIndexer):
    """MefIndexer."""

    record_cls = MefRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, op_type='index', doc_type='mef')
