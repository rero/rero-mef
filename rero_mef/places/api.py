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

from rero_mef.places.mef.api import build_ref_string

from ..api import Action, ReroIndexer, ReroMefRecord


class PlaceRecord(ReroMefRecord):
    """Place record class."""

    name = None

    @classmethod
    def create(cls, data, id_=None, delete_pid=False, dbcommit=False,
               reindex=False, md5=True, **kwargs):
        """Create a new places record."""
        return super().create(
            data=data,
            id_=id_,
            delete_pid=delete_pid,
            dbcommit=dbcommit,
            reindex=reindex,
            md5=True,
            **kwargs
        )

    def delete(self, force=False, dbcommit=False, delindex=False):
        """Delete agent from MEF record."""
        from rero_mef.places import PlaceMefRecord

        for mef_record in PlaceMefRecord.get_mef(self.pid, self.name):
            mef_record.delete_ref(self, dbcommit=dbcommit, reindex=delindex)
        return super().delete(
            force=force,
            dbcommit=dbcommit,
            delindex=delindex
        )

    def create_or_update_mef(self, dbcommit=False, reindex=False):
        """Create or update MEF and VIAF record.

        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :returns: MEF record, MEF action
        """
        from rero_mef.places import PlaceMefRecord

        mef_data = {}
        if mef_records := PlaceMefRecord.get_mef(self.pid, self.name):
            mef_data = mef_records[0]

        if self.deleted and not mef_data.get('deleted'):
            mef_data['deleted'] = self.deleted

        ref_string = build_ref_string(
            place=self.name,
            place_pid=self.pid
        )
        mef_data[self.name] = {'$ref': ref_string}

        if mef_records:
            mef_action = Action.UPDATE
            mef_record = mef_data.replace(
                data=mef_data,
                dbcommit=dbcommit,
                reindex=reindex
            )
        else:
            mef_action = Action.CREATE
            mef_record = PlaceMefRecord.create(
                data=mef_data,
                dbcommit=dbcommit,
                reindex=reindex,
            )
        if reindex:
            PlaceMefRecord.flush_indexes()
        return mef_record, {mef_record.pid: mef_action}

    @classmethod
    def get_online_record(cls, id, debug=False):
        """Get online Record.

        Has to be overloaded in agent class.
        """
        raise NotImplementedError()

    def reindex(self, forceindex=False):
        """Reindex record."""
        from .mef.api import PlaceMefRecord
        result = super().reindex(forceindex=forceindex)
        # reindex MEF records
        for mef_record in PlaceMefRecord.get_mef(self.pid, self.name):
            mef_record.reindex(forceindex=forceindex)
        return result


class PlaceIndexer(ReroIndexer):
    """Indexing class for places."""
