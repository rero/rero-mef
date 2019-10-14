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

from flask import current_app
from invenio_records_rest.links import default_links_factory_with_additional
from invenio_search.api import RecordsSearch

from .fetchers import mef_id_fetcher
from .minters import mef_id_minter
from .models import MefAction, MefMetadata
from .providers import MefProvider
from ..api import AuthRecord, AuthRecordIndexer
from ..utils import add_schema


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
        """Buid url for agency's api."""
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
        key = '{agency}{identifier}'.format(
            agency=agency, identifier='.pid')
        search = MefSearch()
        result = search.query(
            'match', **{key: agency_pid}).source(includes=['pid']).scan()
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
        ).source(includes=['pid', key]).scan()
        for result in results:
            result_dict = result.to_dict()
            yield result_dict.get(agency, {}).get('pid'),\
                result_dict.get('pid')

    @classmethod
    def get_mef_by_viaf_pid(cls, viaf_pid):
        """Get mef record by agency pid value."""
        search = MefSearch()
        result = search.filter(
            'term', viaf_pid=viaf_pid).source(includes=['pid']).scan()
        try:
            mef_pid = next(result).pid
            return cls.get_record_by_pid(mef_pid)
        except StopIteration:
            return None

    @classmethod
    def create_or_update(cls, viaf_record, action=None, agency=None,
                         agency_pid=None, delete_pid=True, dbcommit=False,
                         reindex=False, test_md5=False, **kwargs):
        """Create, update or delete Mef record."""
        mef_record_from_viaf = None
        if viaf_record:
            viaf_pid = viaf_record.pid
            mef_record_from_viaf = cls.get_mef_by_viaf_pid(
                viaf_pid=viaf_pid
            )
            mef_record_from_agency = cls.get_mef_by_agency_pid(
                agency_pid=agency_pid, agency=agency
            )
            ref_string = cls.build_ref_string(
                agency=agency, agency_pid=agency_pid
            )
            if action in [MefAction.UPDATE, MefAction.CREATE]:
                if mef_record_from_viaf:
                    if mef_record_from_agency:
                        mef_record_from_viaf.reindex()
                    else:
                        mef_record_from_viaf[agency] = {'$ref': ref_string}
                        mef_record_from_viaf.update(
                            mef_record_from_viaf,
                            dbcommit=dbcommit,
                            reindex=reindex
                        )
                else:
                    if not mef_record_from_agency:
                        with current_app.app_context():
                            data = {
                                agency: {'$ref': ref_string},
                                'viaf_pid': viaf_pid
                            }
                            data = add_schema(data, 'mef')
                            cls.create(
                                data,
                                id_=None,
                                delete_pid=True,
                                dbcommit=dbcommit,
                                reindex=reindex
                            )
                            action = MefAction.CREATE
                    else:
                        raise NotImplementedError
            elif action == MefAction.DELETE:
                if mef_record_from_viaf:
                    mef_record_from_viaf.pop(agency, None)
                    test_set = set(('bnf', 'gnd', 'idref', 'rero'))
                    if test_set <= set(mef_record_from_viaf):
                        mef_record_from_viaf.update(
                            mef_record_from_viaf,
                            dbcommit=dbcommit,
                            reindex=reindex,
                        )
                    else:
                        mef_record_from_viaf.delete(dbcommit=True,
                                                    delindex=True)
                        mef_record_from_viaf = None
                        action = MefAction.DELETEMEF
            elif action == MefAction.UPTODATE:
                pass
            else:
                raise NotImplementedError
        return mef_record_from_viaf, action, None

    @property
    def links(cls, pid, record=None, **kwargs):
        """Link factory."""
        return default_links_factory_with_additional(
            dict(test_link='{scheme}://{host}/{pid.pid_value}'))


class MefIndexer(AuthRecordIndexer):
    """MefIndexer."""

    record_cls = MefRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, op_type='index', doc_type='mef')
