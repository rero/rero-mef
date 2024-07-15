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

from rero_mef.places.mef.api import build_ref_string

from ..api import Action, ReroIndexer, ReroMefRecord


class PlaceRecord(ReroMefRecord):
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
        """Delete agent from MEF record."""
        from rero_mef.places import PlaceMefRecord

        for mef_record in PlaceMefRecord.get_mef(self.pid, self.name):
            mef_record.delete_ref(self, dbcommit=dbcommit, reindex=delindex)
        return super().delete(force=force, dbcommit=dbcommit, delindex=delindex)

    def create_or_update_mef(self, dbcommit=False, reindex=False):
        """Create or update MEF and VIAF record.

        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :returns: MEF record, MEF action
        """
        actions = {}
        from rero_mef.places import (
            PlaceGndRecord,
            PlaceIdrefRecord,
            PlaceIdrefSearch,
            PlaceMefRecord,
        )

        mef_data = {}
        pid = self.pid
        name = self.name
        # find IDREF MEF record and clean old GND MEF records
        if isinstance(self, PlaceGndRecord):
            query = (
                PlaceIdrefSearch()
                .filter("term", identifiedBy__source="GND")
                .filter("term", identifiedBy__value=f"(DE-101){pid}")
            )
            if idref_pids := [hit.pid for hit in query.scan()]:
                # get latest IDREF MEF data.
                mef_data = PlaceMefRecord.get_latest(
                    pid_type="idref", pid=idref_pids[0]
                )
                # clean old GND MEF records
                for mef_record in PlaceMefRecord.get_mef(self.pid, self.name):
                    mef_record.delete_ref(self, dbcommit=dbcommit, reindex=reindex)
                    actions[mef_record.pid] = Action.DELETE_AGENT
                # get the IDREF MEF record
                if mef_pid := mef_data.get("pid"):
                    mef_data = PlaceMefRecord.get_record_by_pid(mef_pid)

        # if we don't have a MEF record try to find one
        if not mef_data and (mef_records := PlaceMefRecord.get_mef(pid, name)):
            mef_data = mef_records[0]
        # correct GND ref from IDREF
        update_gnd_pid_for_mef = None
        if isinstance(self, PlaceIdrefRecord):
            gnd_ref_pid = mef_data.get("gnd", {}).get("$ref", "").split("/")[-1]
            # find GND pid from identifiedBy
            for identified_by in self.get("identifiedBy"):
                value = identified_by.get("value")
                if identified_by.get("source") == "GND" and value.startswith(
                    "(DE-101)"
                ):
                    gnd_pid = value.replace("(DE-101)", "")
                    if gnd_ref_pid and gnd_ref_pid != gnd_pid:
                        mef_data.pop("gnd", None)
                        update_gnd_pid_for_mef = gnd_ref_pid
                    # if we have a GND record add the $ref for MEF
                    if gnd_rec := PlaceGndRecord.get_record_by_pid(gnd_pid):
                        mef_data["gnd"] = {
                            "$ref": build_ref_string(place="gnd", place_pid=gnd_pid)
                        }
                    # clean old GND MEF records
                    for mef_record in PlaceMefRecord.get_mef(gnd_pid, "gnd"):
                        if mef_record.pid != mef_data.get("pid"):
                            mef_record.pop("gnd", None)
                            mef_record.replace(
                                data=mef_record, dbcommit=dbcommit, reindex=reindex
                            )
                            actions[mef_record.pid] = Action.DELETE_AGENT

        mef_data[self.name] = {
            "$ref": build_ref_string(place=self.name, place_pid=self.pid)
        }
        if mef_data.get("pid"):
            mef_action = Action.UPDATE
            mef_record = mef_data.replace(
                data=mef_data, dbcommit=dbcommit, reindex=reindex
            )
        else:
            if self.deleted and not mef_data.get("deleted"):
                mef_data["deleted"] = self.deleted
            mef_action = Action.CREATE
            mef_record = PlaceMefRecord.create(
                data=mef_data,
                dbcommit=dbcommit,
                reindex=reindex,
            )
        actions[mef_record.pid] = mef_action
        if reindex:
            PlaceMefRecord.flush_indexes()
        if update_gnd_pid_for_mef and (
            gnd_rec := PlaceGndRecord.get_record_by_pid(update_gnd_pid_for_mef)
        ):
            _, m_action = gnd_rec.create_or_update_mef(
                dbcommit=dbcommit, reindex=reindex
            )
            actions.update(m_action)
        return mef_record, actions

    @classmethod
    def get_online_record(cls, id_, debug=False):
        """Get online Record.

        :param id_: Id of online record.
        :param debug: Debug print.
        :returns: record or None
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
