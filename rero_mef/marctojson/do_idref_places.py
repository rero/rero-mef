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
"""Marctojsons transformer for IdRef records."""

import contextlib
from datetime import datetime, timezone

from rero_mef.marctojson.helper import (
    build_string_from_field,
    build_string_list_from_fields,
)


class Transformation(object):
    """Transformation MARC21 to JSON for Idref concept."""

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
        if fields_008 := self.marc.get_fields("008"):
            for func in dir(self):
                if func.startswith("trans"):
                    func = getattr(self, func)
                    func()
        else:
            msg = "No 008"
            if self.logger and self.verbose:
                self.logger.warning(f"NO TRANSFORMATION: {msg}")
            self.json_dict = {"NO TRANSFORMATION": msg}
            self.trans_idref_pid()

    @property
    def json(self):
        """Json data."""
        return self.json_dict or None

    def trans_idref_pid(self):
        """Transformation identifier from field 001."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_pid")
        if field_001 := self.marc.get_fields("001"):
            self.json_dict["pid"] = field_001[0].data
            self.json_dict["type"] = "bf:Place"

    def trans_idref_bnf_type(self):
        """Transformation bnf_type from field 008."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_bnf_type")
        self.json_dict["bnf_type"] = "sujet Rameau"

    def trans_idref_identifier(self):
        """Transformation identifier from field 003 033."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_identifier")
        identifiers = self.json_dict.get("identifiedBy", [])
        if field_003 := self.marc.get_fields("003"):
            identifiers.append(
                {"type": "uri", "value": field_003[0].data.strip(), "source": "IDREF"}
            )
        for field_033 in self.marc.get_fields("033"):
            if field_033.get("2") and field_033["2"] == "BNF" and field_033.get("a"):
                identifiers.append(
                    {"type": "uri", "value": field_033["a"].strip(), "source": "BNF"}
                )
        if identifiers:
            self.json_dict["identifiedBy"] = identifiers

    def trans_idref_relation_pid(self):
        """Transformation old pids 035 $a $9 = sudoc."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_relation_pid")
        for field_035 in self.marc.get_fields("035"):
            subfield_a = field_035.get("a")
            if isinstance(subfield_a, list):
                subfield_a = subfield_a[0]
            subfield_2 = field_035.get("2")
            if isinstance(subfield_2, list):
                subfield_2 = subfield_2[0]
            subfield_9 = field_035.get("9")
            if isinstance(subfield_9, list):
                subfield_9 = subfield_9[0]
            if subfield_a and subfield_9 == "sudoc":
                self.json_dict["relation_pid"] = {
                    "value": field_035["a"],
                    "type": "redirect_from",
                }
            elif subfield_2:
                identified_by = self.json_dict.get("identifiedBy", [])
                identified_by.append(
                    {
                        "source": subfield_2.upper(),
                        "type": "uri" if subfield_a.startswith("http") else "bf:Nbn",
                        "value": subfield_a,
                    }
                )
                self.json_dict["identifiedBy"] = identified_by

    def trans_idref_deleted(self):
        """Transformation deleted leader 5 == d."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_deleted")
        if self.marc.leader[5] == "d":
            self.json_dict["deleted"] = datetime.now(timezone.utc).isoformat()

    def trans_idref_authorized_access_point(self):
        """Transformation authorized_access_point from field 215."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_authorized_access_point")
        tag = "215"
        subfields = {"a": ", ", "x": " - ", "y": " - ", "z": " - "}
        try:
            if authorized_ap := build_string_from_field(self.marc[tag], subfields):
                self.json_dict["authorized_access_point"] = authorized_ap
        except Exception as err:
            self.json_dict["authorized_access_point"] = f"TAG: {tag} NOT FOUND"

    def trans_idref_variant_access_point(self):
        """Transformation variant_access_point from field 415."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_variant_access_point")
        tag = "415"
        subfields = {"a": ", ", "x": " - ", "y": " - ", "z": " - "}
        if variant_access_points := build_string_list_from_fields(
            self.marc, tag, subfields
        ):
            self.json_dict["variant_access_point"] = variant_access_points

    def trans_idref_relation(self):
        """Transformation broader related narrower 515."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_relation")
        relations = {}
        for tag in ["515"]:
            for field in self.marc.get_fields(tag):
                relation_type = None
                if subfield_5 := field.get("5"):
                    if subfield_5[0] == "g":
                        relation_type = "broader"
                    elif subfield_5[0] == "h":
                        relation_type = "narrower"
                    elif subfield_5[0] == "z":
                        relation_type = "related"
                if relation_type:
                    relations.setdefault(relation_type, [])
                    # TODO: $ref relation
                    # if subfield_3 := field.get('3'):
                    #     relations[relation_type].append({
                    #         '$ref':
                    #         f'https://.../concepts/idref/{subfield_3}'
                    #     })
                    # else:
                    subfields = {"a": ", ", "x": " - ", "y": " - ", "z": " - "}
                    if authorized_ap := build_string_from_field(field, subfields):
                        relations.setdefault(relation_type, [])
                        relations[relation_type].append(
                            {"authorized_access_point": authorized_ap}
                        )
        for relation, value in relations.items():
            if value:
                self.json_dict[relation] = value

    def trans_idref_classification(self):
        """Transformation classification from field 686."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_classification")
        classifications = []
        for field_686 in self.marc.get_fields("686"):
            if field_686.get("a"):
                classification = {
                    "type": "bf:ClassificationDdc",
                    "classificationPortion": field_686["a"].strip(),
                }
                if field_686.get("c"):
                    classification["name"] = field_686["c"]
                classifications.append(classification)
        if classifications:
            self.json_dict["classification"] = classifications

    def trans_idref_close_match(self):
        """Transformation closeMatch from field 822."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_close_match")
        close_matchs = []
        for field_822 in self.marc.get_fields("822"):
            with contextlib.suppress(Exception):
                close_match = {}
                if field_822.get("a") and field_822.get("2"):
                    close_match = {
                        "authorized_access_point": field_822["a"].strip(),
                        "source": field_822["2"].strip(),
                    }
                    if field_822.get("u"):
                        close_match["identifiedBy"] = {
                            "type": "uri",
                            "value": field_822["u"].strip(),
                            "source": field_822["2"].strip(),
                        }
                if close_match:
                    close_matchs.append(close_match)
        if close_matchs:
            self.json_dict["closeMatch"] = close_matchs

    def trans_idref_note(self):
        """Transformation notes from field.

        810 $a: dataSource
        815 $a: dataNotFound
        300 $a: general
        330 $a: general
        356 $a: general
        305 $a: seeReference
        310 $a: seeReference
        320 $a: seeReference
        """
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_note")
        notes = {
            "dataSource": [],
            "dataNotFound": [],
            "general": [],
            "seeReference": [],
        }
        for field in self.marc.get_fields("810"):
            if field.get("a"):
                notes["dataSource"].append(field["a"].strip())
        for field in self.marc.get_fields("815"):
            if field.get("a"):
                notes["dataNotFound"].append(field["a"].strip())
        for field in self.marc.get_fields("300", "330", "356"):
            if field.get("a"):
                notes["general"].append(field["a"].strip())
        for field in self.marc.get_fields("305", "310", "320"):
            if field.get("a"):
                notes["seeReference"].append(field["a"].strip())
        for note, value in notes.items():
            if value:
                self.json_dict.setdefault("note", [])
                self.json_dict["note"].append({"noteType": note, "label": value})
