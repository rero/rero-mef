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

"""Marctojsons transformer for GND records."""
# https://www.dnb.de/EN/Professionell/Metadatendienste/Datenbezug/GND_Aenderungsdienst/gndAenderungsdienst_node.html

import contextlib
from datetime import datetime, timezone

from rero_mef.marctojson.helper import (
    build_string_from_field,
    build_string_list_from_fields,
    get_source_and_id,
)

RECORD_TYPES = {
    "p": "bf:Person",
    "b": "bf:Organisation",
    "f": "bf:Organisation",
    "g": "bf:Place",
    "s": "bf:Topic",
    "u": "bf:Title",
}


class Transformation(object):
    """Transformation MARC21 to JSON for GND autority concept."""

    def __init__(self, marc, logger=None, verbose=False, transform=True):
        """Constructor."""
        self.marc = marc
        self.logger = logger
        self.verbose = verbose
        self.json_dict = {}
        if transform:
            self._transform()

    def _transform(self):
        """Call the transformation functions."""
        for func in dir(self):
            if func.startswith("trans"):
                func = getattr(self, func)
                func()

    @property
    def json(self):
        """Json data."""
        return self.json_dict or None

    def trans_gnd_deleted(self):
        """Transformation deleted leader 5.

        $c: Redirect notification
        $x: Redirect
        $c: Deletion notification
        $d: Deletion

        https://www.dnb.de/EN/Professionell/Metadatendienste/Datenbezug/
        GND_Aenderungsdienst/gndAenderungsdienst_node.html
        """
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_deleted")
        if self.marc.leader[5] in ["c", "d", "x"]:
            self.json_dict["deleted"] = datetime.now(timezone.utc).isoformat()

    def trans_gnd_pid(self):
        """Transformation pid from field 001."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_pid")
        if field_001 := self.marc.get_fields("001"):
            self.json_dict["pid"] = field_001[0].data
            self.json_dict["type"] = "bf:Topic"

    def trans_gnd_identifier(self):
        """Transformation identifier from field 024, 035."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_identifier")
        fields_024 = self.marc.get_fields("024")
        for field_024 in fields_024:
            subfield_0 = field_024.get("0")
            if isinstance(subfield_0, list):
                subfield_0 = subfield_0[0]
            subfield_2 = field_024.get("2")
            if isinstance(subfield_2, list):
                subfield_2 = subfield_2[0]
            if subfield_0 and subfield_2:
                self.json_dict.setdefault("identifiedBy", []).append(
                    {
                        "source": subfield_2.upper(),
                        "type": "uri",
                        "value": subfield_0,
                    }
                )
        for field_035 in self.marc.get_fields("035"):
            if field_035.get("a"):
                subfield_a = field_035["a"]
                if subfield_a.startswith("(DE-101)") or subfield_a.startswith(
                    "(DE-588)"
                ):
                    self.json_dict.setdefault("identifiedBy", []).append(
                        {
                            "source": "GND",
                            "type": "bf:Nbn",
                            "value": subfield_a,
                        }
                    )

    def trans_gnd_authorized_access_point(self):
        """Transformation authorized_access_point 150."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_authorized_access_point")
        tag = "150"
        subfields = {"a": ", ", "g": " , ", "x": " - "}
        tag_grouping = [
            {
                "subtags": "g",
                "start": " (",
                "end": ")",
                "delimiter": "",
                "subdelimiter": ", ",
            }
        ]
        try:
            if authorized_ap := build_string_from_field(
                field=self.marc[tag], subfields=subfields, tag_grouping=tag_grouping
            ):
                self.json_dict["authorized_access_point"] = authorized_ap
        except Exception:
            self.json_dict["authorized_access_point"] = f"TAG: {tag} NOT FOUND"

    def trans_gnd_variant_access_point(self):
        """Transformation variant_access_point 450."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_variant_access_point")
        tag = "450"
        subfields = {"a": ", ", "g": " , "}
        tag_grouping = [
            {
                "subtags": "g",
                "start": " (",
                "end": ")",
                "delimiter": "",
                "subdelimiter": ", ",
            }
        ]
        if variant_access_point := build_string_list_from_fields(
            record=self.marc, tag=tag, subfields=subfields, tag_grouping=tag_grouping
        ):
            self.json_dict["variant_access_point"] = variant_access_point

    def trans_gnd_relation_pid(self):
        """Transformation relation pids 682 $0."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_relation")
        fields_682 = self.marc.get_fields("682")
        for field_682 in fields_682:
            if field_682.get("i") and field_682["i"] == "Umlenkung":
                subfields_0 = field_682.get_subfields("0")
                for subfield_0 in subfields_0:
                    if subfield_0.startswith("(DE-101)"):
                        self.json_dict["relation_pid"] = {
                            "value": subfield_0.replace("(DE-101)", ""),
                            "type": "redirect_to",
                        }

    def trans_gnd_relation(self):
        """Transformation relation 550."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_relation")
        relations = {}
        for field_550 in self.marc.get_fields("550"):
            authorized_aps = set()
            with contextlib.suppress(Exception):
                relation_type = "related"
                if subfield_4 := field_550.get("4"):
                    if subfield_4 in ["nach", "obal", "obge", "obin"]:
                        relation_type = "broader"
                    elif subfield_4[0] in ["vorg"]:
                        relation_type = "narrower"

                subfields = {"a": ", ", "g": " , "}
                tag_grouping = [
                    {
                        "subtags": "g",
                        "start": " (",
                        "end": ")",
                        "delimiter": "",
                        "subdelimiter": ", ",
                    }
                ]
                if authorized_ap := build_string_from_field(
                    field=field_550, subfields=subfields, tag_grouping=tag_grouping
                ):
                    relations.setdefault(relation_type, [])
                    if authorized_ap not in authorized_aps:
                        authorized_aps.add(authorized_ap)
                        relations[relation_type].append(
                            {"authorized_access_point": authorized_ap}
                        )
        for relation, value in relations.items():
            if value:
                self.json_dict[relation] = value

    def trans_gnd_match(self):
        """Transformation closeMatch and exactMatch from field 750."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_match")
        for field_750 in self.marc.get_fields("750"):
            with contextlib.suppress(Exception):
                match_type = None
                subfield_i = field_750["i"]
                if subfield_i == "Aequivalenz":
                    match_type = "closeMatch"
                elif subfield_i == "exakte Aequivalenz":
                    match_type = "exactMatch"
                if match_type:
                    subfields = {
                        "a": ", ",
                        "g": " , ",
                        "x": " - ",
                        "y": " - ",
                        "z": " - ",
                    }
                    tag_grouping = [
                        {
                            "subtags": "g",
                            "start": " (",
                            "end": ")",
                            "delimiter": "",
                            "subdelimiter": ", ",
                        }
                    ]
                    if authorized_ap := build_string_from_field(
                        field=field_750, subfields=subfields, tag_grouping=tag_grouping
                    ):
                        match_data = {
                            "authorized_access_point": authorized_ap,
                            "source": "GND",
                        }
                        identified_by = []
                        other_source = None
                        for subfield_0 in field_750.get_subfields("0"):
                            if subfield_0.startswith("http"):
                                identified_by.insert(
                                    0,
                                    {
                                        "type": "uri",
                                        "value": subfield_0,
                                    },
                                )
                                if other_source:
                                    identified_by[0]["source"] = other_source
                            else:
                                source, id_ = get_source_and_id(subfield_0)
                                if source:
                                    insert_pos = -1
                                    if source != "GND":
                                        other_source = source
                                        match_data["source"] = other_source
                                        insert_pos = 0
                                    identified_by.insert(
                                        insert_pos,
                                        {
                                            "source": source,
                                            "type": "bf:Nbn",
                                            "value": id_,
                                        },
                                    )
                        if identified_by:
                            match_data["identifiedBy"] = identified_by
                        self.json_dict.setdefault(match_type, []).append(match_data)

    def trans_gnd_note(self):
        """Transformation notes from field.

        670 $a - $u: dataSource
        677 $a: general
        678 $a: general
        680 $a: general
        """
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_note")
        notes = {
            "dataSource": [],
            "dataNotFound": [],
            "general": [],
            "seeReference": [],
        }
        for field in self.marc.get_fields("677", "678", "680"):
            if field.get("a"):
                notes["general"].append(field["a"].strip())
            if field.get("b"):
                notes["general"].append(field["b"].strip())
        for field in self.marc.get_fields("670"):
            if field.get("a") and field.get("u"):
                fields_u = field.get("u")
                if isinstance(fields_u, str):
                    fields_u = [fields_u]
                info = f"{field['a'].strip()} - {', '.join(fields_u)}"
                notes["dataSource"].append(info)
        for note, value in notes.items():
            if value:
                self.json_dict.setdefault("note", [])
                self.json_dict["note"].append({"noteType": note, "label": value})
