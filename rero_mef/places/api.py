# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2024 RERO
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

from rero_mef.api import ConceptPlaceRecord, EntityIndexer


class PlaceRecord(ConceptPlaceRecord):
    """Place record class."""

    name = None

    @classmethod
    def create(
        cls,
        data,
        id_=None,
        delete_pid=False,
        dbcommit=False,
        reindex=False,
        md5=True,
        **kwargs,
    ):
        """Create a new places record."""
        return super().create(
            data=data,
            id_=id_,
            delete_pid=delete_pid,
            dbcommit=dbcommit,
            reindex=reindex,
            md5=True,
            **kwargs,
        )

    def delete(self, force=False, dbcommit=False, delindex=False):
        """Delete entity from MEF record."""
        from rero_mef.places import PlaceMefRecord

        for mef_record in PlaceMefRecord.get_mef(self.pid, self.name):
            mef_record.delete_ref(self, dbcommit=dbcommit, reindex=delindex)
        return super().delete(force=force, dbcommit=dbcommit, delindex=delindex)

    def reindex(self, forceindex=False):
        """Reindex record."""
        from .mef.api import PlaceMefRecord

        result = super().reindex(forceindex=forceindex)
        # reindex MEF records
        for mef_record in PlaceMefRecord.get_mef(self.pid, self.name):
            mef_record.reindex(forceindex=forceindex)
        return result


class PlaceIndexer(EntityIndexer):
    """Indexing class for places."""
