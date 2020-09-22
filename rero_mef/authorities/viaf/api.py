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

import click
import requests
from elasticsearch_dsl.query import Q
from invenio_db import db
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_rest.utils import obj_or_import_string
from invenio_search import current_search
from invenio_search.api import RecordsSearch

from .fetchers import viaf_id_fetcher
from .minters import viaf_id_minter
from .models import ViafMetadata
from .providers import ViafProvider
from ..api import AuthRecord, AuthRecordIndexer
from ..mef.api import MefRecord
from ..mef.models import MefAction
from ..models import AgencyAction
from ..utils import add_schema, get_agencies_endpoints, get_agency_class, \
    progressbar


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
        if pid_type == 'mef':
            mef_record = MefRecord.get_record_by_pid(pid)
            viaf_pid = mef_record.get('viaf_pid')
            return cls.get_record_by_pid(viaf_pid)
        if pid_type == 'viaf':
            return cls.get_record_by_pid(pid)
        result = search.filter(
            'term', **{pid_type: pid}).source(['pid']).scan()
        try:
            viaf_pid = next(result).pid
            return cls.get_record_by_pid(viaf_pid)
        except StopIteration:
            return None

    @classmethod
    def create_or_update(cls, data, id_=None, dbcommit=False,
                         reindex=False, **kwargs):
        """Create or update viaf record."""
        pid = data['pid']
        record = cls.get_record_by_pid(pid)
        if record:
            data['$schema'] = record['$schema']
            data['pid'] = record['pid']
            record.update(
                data=data,
                dbcommit=dbcommit,
                reindex=reindex
            )
            viaf_action = AgencyAction.UPDATE
        else:
            record = cls.create(
                data=data,
                delete_pid=False,
                dbcommit=dbcommit,
                reindex=reindex
            )
            viaf_action = AgencyAction.CREATE
        mef_record = MefRecord.get_mef_by_viaf_pid(record.pid)
        mef_data, mef_has_refs = MefRecord.mef_data_from_viaf(mef_record, data)
        if mef_record:
            mef_action = MefAction.REPLACE
            mef_record = mef_record.replace(
                data=mef_data,
                dbcommit=dbcommit,
                reindex=reindex
            )
        else:
            if mef_has_refs:
                mef_action = MefAction.CREATE
                mef_data = add_schema(mef_data, 'mef')
                mef_record = MefRecord.create(
                    data=mef_data,
                    id_=None,
                    delete_pid=True,
                    dbcommit=dbcommit,
                    reindex=reindex
                )
            else:
                mef_action = MefAction.DELETE
        return record, viaf_action, mef_action

    def create_mef_and_agencies(self, dbcommit=False, reindex=False,
                                test_md5=False, online=False,
                                verbose=False):
        """Create MEF and agencies records."""
        actions = {}
        for agency, agency_data in get_agencies_endpoints().items():
            actions[agency] = {
                'mef': MefAction.DISCARD,
                'agency': AgencyAction.DISCARD
            }
            pid_name = '{agency}_pid'.format(agency=agency)
            pid_value = self.get(pid_name)
            if pid_value:
                agency_class = obj_or_import_string(
                    agency_data.get('record_class')
                )
                try:
                    PersistentIdentifier.get(
                        agency_class.provider.pid_type,
                        pid_value
                    )
                except PIDDoesNotExistError:
                    # try to get the agency record online
                    if online:
                        record, a_action, m_action = \
                            agency_class.get_online_record(
                                id=pid_value,
                                dbcommit=dbcommit,
                                reindex=reindex,
                                test_md5=test_md5,
                                verbose=verbose
                            )
                        if record:
                            agency_class.update_indexes()
                            MefRecord.update_indexes()
                        actions[agency] = {
                            'mef': m_action,
                            'agency': a_action
                        }

        mef_record = MefRecord.get_mef_by_viaf_pid(self.pid)
        if not mef_record:
            mef_data, mef_has_refs = MefRecord.mef_data_from_viaf(None, self)
            if mef_has_refs:
                actions['mef'] = MefAction.CREATE
                mef_data = add_schema(mef_data, 'mef')
                mef_record = MefRecord.create(
                    data=mef_data,
                    id_=None,
                    delete_pid=True,
                    dbcommit=dbcommit,
                    reindex=reindex
                )
                MefRecord.update_indexes()
        if verbose:
            msgs = []
            for key, value in actions.items():
                if key == 'mef':
                    msgs.insert(0, '{key}: {m_action}'.format(
                        key=key,
                        m_action=value
                    ))
                else:
                    if value['agency'] != AgencyAction.DISCARD and \
                            value['mef'] != MefAction.DISCARD:
                        msgs.append('{key}: {a_action} {m_action}'.format(
                            key=key,
                            a_action=value['agency'],
                            m_action=value['mef']
                        ))
            if msgs:
                click.echo(
                    'Create MEF viaf pid:{pid} > {actions}'.format(
                        pid=self.pid,
                        actions=', '.join(msgs)
                    )
                )
        return actions

    def create_mef(self, dbcommit=False, reindex=False, verbose=False):
        """Create MEF records."""
        return MefAction.DISCARD

    @classmethod
    def get_online_viaf_record(cls, viaf_source_code, pid, format=None):
        """Get VIAF record.

        Get's the VIAF record from:
        http://www.viaf.org/viaf/sourceID/{source_code}|{pid}

        :param viaf_source_code: Authority source code
        :param pid: pid for authority source code
        :param format: raw = get the not transformed VIAF record
                       link = get the VIAF link record
        :returns: VIAF record as json
        """
        source_code = {
            'DNB': 'gnd_pid',
            'SUDOC': 'idref_pid',
            'RERO': 'rero_pid'
        }
        viaf_format = '/viaf.json'
        if format == 'link':
            viaf_format = '/justlinks.json'
            format = 'raw'
        url = '{viaf_url}/{viaf_source_code}|{pid}{format}'.format(
            viaf_url='http://www.viaf.org/viaf/sourceID',
            viaf_source_code=viaf_source_code,
            pid=pid,
            format=viaf_format
        )
        response = requests.get(url)
        result = {}
        if response.status_code == requests.codes.ok:
            if format == 'raw':
                return response.json()
            data_json = response.json()
            result['pid'] = data_json['viafID']
            sources = data_json.get('sources', {}).get('source')
            if isinstance(sources, dict):
                sources = [sources]
            for source in sources:
                text = source.get('#text', '|').split('|')
                if text[0] in source_code:
                    result[source_code[text[0]]] = text[1]
        return result or None

    @classmethod
    def update_indexes(cls):
        """Update indexes."""
        index = 'viaf-viaf-person-v0.0.1'
        current_search.flush_and_refresh(index=index)

    def get_agencies_records(self):
        """Get agencies."""
        agencies_record = {}
        agencies_pid_type = {}
        agencies_endpoints = get_agencies_endpoints()
        for agency, agency_data in agencies_endpoints.items():
            agencies_pid_type['{agency}_pid'.format(agency=agency)] = \
                obj_or_import_string(agency_data.get('record_class'))
        for data in self:
            if data in agencies_pid_type:
                record = agencies_pid_type[data].get_record_by_pid(self[data])
                if record:
                    agencies_record[data] = record
        return agencies_record

    def delete(self, dbcommit=False, delindex=False):
        """Delete record and persistent identifier."""
        agencies_records = self.get_agencies_records()
        # delete viaf_pid from Mef record
        from ..mef.api import MefRecord
        mef_record = MefRecord.get_mef_by_viaf_pid(self.pid)
        if mef_record:
            mef_record.pop('viaf_pid', None)
            mef_record.replace(mef_record, dbcommit=dbcommit, reindex=True)
        # delete Viaf record
        persistent_identifier = self.get_persistent_identifier(self.id)
        result = super(AuthRecord, self).delete(force=True)
        if dbcommit:
            self.dbcommit()
        if delindex:
            self.delete_from_index()
            self.update_indexes()
        # realy delete persistent identifier
        db.session.delete(persistent_identifier)
        if dbcommit:
            db.session.commit()

        # delete agencies refs from Mef record
        mef_actions = []
        if mef_record:
            for data, agency_record in agencies_records.items():
                agency_record.delete_from_mef(dbcommit=dbcommit, reindex=True,
                                              verbose=False)
                mef_record, mef_action, has_viaf = \
                    agency_record.create_or_update_mef_viaf_record(
                        dbcommit=dbcommit, reindex=True)
                mef_actions.append(
                    '{data}: {apid} mef: {pid} {action} {viaf}'.format(
                        data=data,
                        apid=agency_record.get('pid'),
                        pid=mef_record.get('pid'),
                        action=str(mef_action),
                        viaf=has_viaf
                    )
                )
                ViafRecord.update_indexes()

        return result, '; '.join(mef_actions)

    def create_or_update_mef_viaf_record(self, dbcommit=False, reindex=False,
                                         online=False):
        """Create or update MEF and VIAF record."""
        return self, MefAction.DISCARD, False

    @classmethod
    def get_missing_agency_pids(cls, agency, verbose=False):
        """Get all missing pids defined in VIAF."""
        pids_db = {}
        pids_viaf = []
        record_class = get_agency_class(agency)
        if verbose:
            click.echo(
                'Get pids from {agency} ...'.format(agency=agency)
            )
        progress = progressbar(
            items=record_class.get_all_pids(),
            length=record_class.count(),
            verbose=verbose
        )
        for pid in progress:
            pids_db[pid] = 1
        if verbose:
            click.echo(
                'Get pids from viaf with {agency} ...'.format(agency=agency)
            )
        agency_pid_name = '{agency}_pid'.format(agency=agency)
        query = ViafSearch().filter('bool', should=[
            Q('exists', field=agency_pid_name)
        ]).source(['pid', agency_pid_name])
        progress = progressbar(
            items=query.scan(),
            length=query.count(),
            verbose=verbose
        )
        for hit in progress:
            viaf_pid = hit.pid
            agency_pid = hit.to_dict().get(agency_pid_name)
            if pids_db.get(agency_pid):
                pids_db.pop(agency_pid)
            else:
                pids_viaf.append(viaf_pid)
        pids_db = [v for v in pids_db]
        return pids_db, pids_viaf


class ViafIndexer(AuthRecordIndexer):
    """ViafIndexer."""

    record_cls = ViafRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, op_type='index', doc_type='viaf')
