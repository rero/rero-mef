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

"""Marctojsons transformer for GND records."""
# https://www.dnb.de/EN/Professionell/Metadatendienste/Datenbezug/GND_Aenderungsdienst/gndAenderungsdienst_node.html

import re
from datetime import datetime, timezone

from rero_mef.marctojson.helper import (
    COUNTRIES,
    COUNTRY_UNIMARC_MARC21,
    LANGUAGES,
    build_string_list_from_fields,
)

PUNCTUATION_POLICY = {
    "#": "No information provided",
    "c": "Punctuation omitted",
    "i": "Punctuation included",
    "u": "Unknown",
}

RECORD_TYPES = {
    "p": "bf:Person",
    "b": "bf:Organisation",
    "f": "bf:Organisation",
    "g": "bf:Place",
    "s": "bf:Topic",
    "u": "bf:Title",
}


class Transformation(object):
    """Transformation MARC21 to JSON for GND autority person."""

    def __init__(self, marc, logger=None, verbose=False, transform=True):
        """Constructor."""
        self.marc = marc
        self.logger = logger
        self.verbose = verbose
        self.json_dict = {}
        self.punctuation = marc.leader[18]
        if transform:
            self._transform()

    def get_type(self):
        """Get type of record.

        Entitäten der GND (Satztypen) 075 $b TYPE $2 gndgen
        - b Körperschaft
        - f Konferenz
        - g Geografikum
        - n Person (nicht individualisiert)
        - p Person (individualisiert)
        - s Sachbegriff
        - u Werk
        """
        for field_075 in self.marc.get_fields("075") or []:
            if field_075.get("2") and field_075["2"] == "gndgen":
                return RECORD_TYPES.get(field_075["b"])

    def _transform(self):
        """Call the transformation functions."""
        record_type = self.get_type()
        if record_type in {"bf:Person", "bf:Organisation"}:
            if self.marc.get_fields("100", "110", "111"):
                for func in dir(self):
                    if func.startswith("trans"):
                        func = getattr(self, func)
                        func()
            else:
                msg = "No 100 or 110 or 111"
                if self.logger and self.verbose:
                    self.logger.warning(f"NO TRANSFORMATION: {msg}")
                self.json_dict = {"NO TRANSFORMATION": msg}
                self.trans_gnd_pid()
        else:
            msg = f"Not a person or organisation: {record_type}"
            if self.logger and self.verbose:
                self.logger.warning(f"NO TRANSFORMATION: {msg}")
            self.json_dict = {"NO TRANSFORMATION": msg}
            self.trans_gnd_pid()

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

    def trans_gnd_relation_pid(self):
        """Transformation relation pids 682 $0.

        https://www.dnb.de/EN/Professionell/Metadatendienste/Datenbezug/
        GND_Aenderungsdienst/gndAenderungsdienst_node.html
        """
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_relation_pid")
        fields_035 = self.marc.get_fields("682")
        for field_035 in fields_035:
            if field_035.get("i") and field_035["i"] == "Umlenkung":
                subfields_0 = field_035.get_subfields("0")
                for subfield_0 in subfields_0:
                    if subfield_0.startswith("(DE-101)"):
                        self.json_dict["relation_pid"] = {
                            "value": subfield_0.replace("(DE-101)", ""),
                            "type": "redirect_to",
                        }

    def trans_gnd_gender(self):
        """Transform gender 375 $a 1 = male, 2 = female, " " = not known."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_gender")
        gender = ""
        if fields_375 := self.marc.get_fields("375"):
            if fields_375[0].get("a"):
                gender_type = fields_375[0]["a"]
                if gender_type == "2":
                    gender = "female"
                elif gender_type == "1":
                    gender = "male"
                elif gender_type == " ":
                    gender = "not known"
            if gender:
                self.json_dict["gender"] = gender

    def trans_gnd_language(self):
        """Transformation language 377 $a."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_language")
        if field_377 := self.marc.get_fields("377"):
            if language_list := [
                language
                for language in field_377[0].get_subfields("a")
                if language in LANGUAGES
            ]:
                self.json_dict["language"] = language_list

    def trans_gnd_pid(self):
        """Transformation pid from field 001."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_pid")
        if field_001 := self.marc.get_fields("001"):
            self.json_dict["pid"] = field_001[0].data

    def trans_gnd_identifier(self):
        """Transformation identifier from field 001."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_identifier")
        fields_024 = self.marc.get_fields("024")
        for field_024 in fields_024:
            subfields_0 = field_024.get("0")
            subfields_2 = field_024.get("2")
            if subfields_0 and subfields_2 == "gnd":
                self.json_dict.setdefault("identifiedBy", []).append(
                    {"type": "uri", "value": subfields_0, "source": "GND"}
                )

    def trans_gnd_birth_and_death_dates(self):
        """Transformation birth_date and death_date."""

        def format_100_date(date_str):
            """Format date from field 100."""
            date_formated = date_str
            if len(date_str) == 8:
                date_formated = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            elif len(date_str) == 4:
                date_formated = date_str[:4]
            return date_formated

        def format_548_date(date_str):
            """Format date from field 548."""
            date_formated = date_str
            if len(date_str) == 4:
                date_formated = date_str[:4]
            return date_formated

        def get_date(dates_per_tag, selector):
            """Get date base on selector ('birth_date' or 'death_date')."""
            if "datx" in dates_per_tag and selector in dates_per_tag["datx"]:
                return dates_per_tag["datx"][selector]
            elif "datl" in dates_per_tag and selector in dates_per_tag["datl"]:
                return dates_per_tag["datl"][selector]
            elif "datb" in dates_per_tag and selector in dates_per_tag["datb"]:
                return dates_per_tag["datb"][selector]
            elif "100" in dates_per_tag and selector in dates_per_tag["100"]:
                return dates_per_tag["100"][selector]
            else:
                return None

        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_birth_and_death_dates")
        dates_per_tag = {}
        if fields_100 := self.marc.get_fields("100"):
            if fields_100[0].get("d"):
                field_100_d = fields_100[0]["d"]
                dates_string = re.sub(r"\s+", " ", field_100_d).strip()
                dates = dates_string.split("-")
                dates_per_tag["100"] = {}
                dates_per_tag["100"]["birth_date"] = format_100_date(dates[0])
                if len(dates) > 1:
                    death_date = format_100_date(dates[1])
                    dates_per_tag["100"]["death_date"] = format_100_date(dates[1])

        for field_548 in self.marc.get_fields("548"):
            if (
                field_548.get("a")
                and field_548.get("4")
                and field_548["4"] in ("datl", "datx", "datb")
            ):
                dates = field_548["a"].split("-")
                if birth_date := format_548_date(dates[0]):
                    dates_per_tag.setdefault(field_548["4"], {})
                    dates_per_tag[field_548["4"]]["birth_date"] = birth_date
                if len(dates) > 1:
                    if death_date := format_548_date(dates[1]):
                        dates_per_tag.setdefault(field_548["4"], {})
                        dates_per_tag[field_548["4"]]["death_date"] = death_date

        if self.marc.get_fields("110") or self.marc.get_fields("111"):
            date_of_establishment = get_date(dates_per_tag, "birth_date")
            date_of_termination = get_date(dates_per_tag, "death_date")
            dates_per_tag.pop("100", None)
            dates_per_tag.pop("datl", None)
            dates_per_tag.pop("datx", None)
            if date_of_establishment:
                self.json_dict["date_of_establishment"] = date_of_establishment
            if date_of_termination:
                self.json_dict["date_of_termination"] = date_of_termination
        else:
            dates_per_tag.pop("datb", None)
            birth_date = get_date(dates_per_tag, "birth_date")
            if birth_date:
                self.json_dict["date_of_birth"] = birth_date
            death_date = get_date(dates_per_tag, "death_date")
            if death_date:
                self.json_dict["date_of_death"] = death_date

    def trans_gnd_biographical_information(self):
        """Transformation biographical_information 678 $abu."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_biographical_information")
        biographical_information = []
        for tag in [678]:
            subfields = {"a": ", ", "b": ", ", "u": ", "}
            biographical_information += build_string_list_from_fields(
                self.marc, str(tag), subfields
            )
        if biographical_information:
            self.json_dict["biographical_information"] = biographical_information

    def trans_gnd_numeration(self):
        """Transformation numeration 100 $b."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_numeration")
        subfields = {"b": " "}
        numeration = build_string_list_from_fields(self.marc, "100", subfields)
        if numeration and numeration[0]:
            self.json_dict["numeration"] = numeration[0]

    def trans_gnd_qualifier(self):
        """Transformation qualifier 100 $c."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_qualifier")
        subfields = {"c": " "}
        qualifier = build_string_list_from_fields(self.marc, "100", subfields)
        if qualifier and qualifier[0]:
            self.json_dict["qualifier"] = qualifier[0]

    def trans_gnd_conference(self):
        """Transformation conference. false: 075 $b = b true: 075 $b = f."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_conference")
        if self.marc.get_fields("110") or self.marc.get_fields("111"):
            if field_075 := self.marc.get("075"):
                if subfields_b := field_075.get("b"):
                    if subfields_b[0] == "f":
                        self.json_dict["conference"] = True
                    elif subfields_b[0] == "b":
                        self.json_dict["conference"] = False

    def trans_gnd_preferred_name(self):
        """Transformation preferred_name 100/110/111."""
        tags = ["100"]
        subfields = {"a": ", ", "b": ", ", "c": ", "}
        if self.marc.get_fields("110") or self.marc.get_fields("111"):
            tags = []
            subfields = {"a": ", ", "b": ". ", "n": ", "}
            if self.marc.get_fields("110"):
                tags.append("110")
            if self.marc.get_fields("111"):
                tags.append("111")
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_preferred_name")
        variant_names = self.json_dict.get("variant_name", [])
        for tag in tags:
            preferred_names = build_string_list_from_fields(
                record=self.marc, tag=tag, subfields=subfields
            )
            for idx, preferred_name in enumerate(preferred_names):
                if idx == 0:
                    self.json_dict["preferred_name"] = preferred_name
                else:
                    variant_names.append(preferred_name)
        if variant_names:
            self.json_dict["variant_name"] = variant_names

    def trans_gnd_authorized_access_point(self):
        """Transformation authorized_access_point 100/110/111."""
        tags = ["100"]
        agent = "bf:Person"
        subfields = {"a": ", ", "b": ", ", "c": ", ", "d": ", ", "x": " - - "}
        if self.marc.get_fields("110", "111"):
            tags = []
            subfields = {
                "a": ", ",
                "b": ". ",
                "n": ", ",
                "d": ", ",
                "c": ", ",
                "e": ". ",
                "g": ". ",
                "k": ". ",
                "t": ". ",
                "x": " - - ",
            }
            if self.marc.get_fields("110"):
                tags.append("110")
            if self.marc.get_fields("111"):
                tags.append("111")
            agent = "bf:Organisation"

        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_authorized_access_point")
        variant_access_points = self.json_dict.get("variant_access_point", [])
        for tag in tags:
            authorized_access_points = build_string_list_from_fields(
                record=self.marc, tag=tag, subfields=subfields
            )
            for authorized_access_point in authorized_access_points:
                self.json_dict["type"] = agent
                if self.json_dict.get("authorized_access_point"):
                    variant_access_points.append(authorized_access_point)
                else:
                    self.json_dict["authorized_access_point"] = authorized_access_point
        if variant_access_points:
            self.json_dict["variant_access_point"] = variant_access_points

    def trans_gnd_variant_name(self):
        """Transformation variant_name 400/410/411."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_variant_name")
        tag = "400"
        subfields = {"a": ", ", "b": ", ", "c": ", "}
        if self.marc.get_fields("410") or self.marc.get_fields("411"):
            subfields = {"a": ", ", "b": ". ", "n": ", "}
            if self.marc.get_fields("410"):
                tag = "410"
            if self.marc.get_fields("411"):
                tag = "411"
        variant_names = self.json_dict.get("variant_name", [])
        if variant_name := build_string_list_from_fields(
            record=self.marc, tag=tag, subfields=subfields
        ):
            variant_names += variant_name
        if variant_names:
            self.json_dict["variant_name"] = variant_names

    def trans_gnd_variant_access_point(self):
        """Transformation variant_access_point 400/410/411."""
        tag = "400"
        subfields = {"a": ", ", "b": ", ", "c": ", ", "d": ", ", "x": " - - "}
        if self.marc.get_fields("410") or self.marc.get_fields("411"):
            subfields = {
                "a": ", ",
                "b": ". ",
                "n": ", ",
                "d": ", ",
                "c": ", ",
                "e": ". ",
                "g": ". ",
                "k": ". ",
                "t": ". ",
                "x": " - - ",
            }
            if self.marc.get_fields("410"):
                tag = "410"
            if self.marc.get_fields("411"):
                tag = "411"
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_variant_access_point")
        if variant_access_point := build_string_list_from_fields(
            record=self.marc, tag=tag, subfields=subfields
        ):
            self.json_dict["variant_access_point"] = variant_access_point

    def trans_gnd_parallel_access_point(self):
        """Transformation parallel_access_point 700/710/711."""
        tag = "700"
        subfields = {"a": ", ", "b": ", ", "c": ", ", "d": ", ", "x": " - - "}
        if self.marc.get_fields("710") or self.marc.get_fields("711"):
            subfields = {
                "a": ", ",
                "b": ". ",
                "n": ", ",
                "d": ", ",
                "c": ", ",
                "e": ". ",
                "g": ". ",
                "k": ". ",
                "t": ". ",
                "x": " - - ",
            }
            if self.marc.get_fields("710"):
                tag = "710"
            if self.marc.get_fields("711"):
                tag = "711"
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_parallel_access_point")
        if parallel_access_point := build_string_list_from_fields(
            record=self.marc, tag=tag, subfields=subfields
        ):
            self.json_dict["parallel_access_point"] = parallel_access_point

    def trans_gnd_country_associated(self):
        """Transformation country_associated 043 $c codes ISO 3166-1."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_gnd_country_associated")
        if fields_043 := self.marc.get_fields("043"):
            if fields_043[0].get("c"):
                country_split = fields_043[0]["c"].split("-")
                if len(country_split) > 1:
                    country = COUNTRY_UNIMARC_MARC21.get(country_split[1])
                    if COUNTRIES.get(country):
                        self.json_dict["country_associated"] = country
