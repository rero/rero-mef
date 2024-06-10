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

"""Marctojsons transformer for IDREF records."""

from datetime import datetime, timezone

from rero_mef.marctojson.helper import (
    COUNTRIES,
    COUNTRY_UNIMARC_MARC21,
    LANGUAGES,
    build_string_list_from_fields,
    remove_trailing_punctuation,
)

LANGUAGE_SCRIPT_CODES = {
    "ba": "latn",
    "ca": "cyrl",
    "da": "jpan",
    "db": "jpan",
    "dc": "jpan",
    "ea": "hani",
    "fa": "arab",
    "ga": "grek",
    "ha": "hebr",
    "ia": "thai",
    "ja": "deva",
    "ka": "kore",
    "la": "taml",
    "ma": "geor",
    "mb": "armn",
}


def get_script_code(field):
    """Get script_code from $7."""
    try:
        subfield_7 = field["7"]
        code = subfield_7[4:6]
        script_code = LANGUAGE_SCRIPT_CODES[code]
    except Exception:
        script_code = "latn"
    return script_code


def build_language_string_list_from_fields(
    record,
    tag,
    subfields,
    punctuation=",",
    spaced_punctuation=":;/-",
    tag_grouping=None,
):
    """Build a list of strings (one per field).

    from the given field tag and given subfields.
    the given separator is used as subfields delimiter.
    """
    if not tag_grouping:
        tag_grouping = []
    fields = record.get_fields(tag)
    field_string_list = []
    for field in fields:
        grouping_data = []
        grouping_code = []
        for code, data in field:
            if code in subfields:
                if isinstance(data, (list, set)):
                    data = subfields[code].join(data)
                data = data.replace("\x98", "")
                data = data.replace("\x9C", "")
                data = data.replace(",,", ",")
                data = remove_trailing_punctuation(
                    data=data,
                    punctuation=punctuation,
                    spaced_punctuation=spaced_punctuation,
                )
                if data := data.strip():
                    for group in tag_grouping:
                        if code in group["subtags"]:
                            code = group["subtags"]
                    if grouping_code and code == grouping_code[-1]:
                        grouping_data[-1].append(data)
                    else:
                        grouping_code.append(code)
                        grouping_data.append([data])
        subfield_string = ""
        for group in zip(grouping_code, grouping_data):
            grouping_start = ""
            grouping_end = ""
            delimiter = subfields.get(group[0])
            subdelimiter = subfields.get(group[0])
            for grouping in tag_grouping:
                if group[0] == grouping["subtags"]:
                    grouping_start = grouping.get("start", "")
                    grouping_end = grouping.get("end", "")
                    delimiter = grouping.get("delimiter", "")
                    subdelimiter = grouping.get("subdelimiter", "")

            if subfield_string:
                subfield_string += (
                    delimiter
                    + grouping_start
                    + subdelimiter.join(group[1])
                    + grouping_end
                )
            else:
                subfield_string = (
                    grouping_start + subdelimiter.join(group[1]) + grouping_end
                )

        if subfield_string:
            script_code = get_script_code(field)
            if script_code == "latn":
                field_string_list.insert(0, subfield_string.strip())
            else:
                field_string_list.append(subfield_string.strip())
    return field_string_list


class Transformation(object):
    """Transformation UNIMARC to JSON for IDREF autority person."""

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
        if self.marc.get_fields("200") or self.marc.get_fields("210"):
            for func in dir(self):
                if func.startswith("trans"):
                    func = getattr(self, func)
                    func()
        else:
            msg = "No 200 or 210"
            if self.logger and self.verbose:
                self.logger.warning(f"NO TRANSFORMATION: {msg}")
            self.json_dict = {"NO TRANSFORMATION": msg}
            self.trans_idref_pid()

    @property
    def json(self):
        """Json data."""
        return self.json_dict or None

    def trans_idref_deleted(self):
        """Transformation deleted leader 5 == d."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_deleted")
        if self.marc.leader[5] == "d":
            self.json_dict["deleted"] = datetime.now(timezone.utc).isoformat()

    def trans_idref_relation_pid(self):
        """Transformation old pids 035 $a $9 = sudoc."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_relation_pid")
        for field_035 in self.marc.get_fields("035"):
            if field_035.get("a") and field_035.get("9") and field_035["9"] == "sudoc":
                self.json_dict["relation_pid"] = {
                    "value": field_035["a"],
                    "type": "redirect_from",
                }

    def trans_idref_gender(self):
        """Transformation gender 120 $a a:female, b: male, -:not known."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_gender")
        if fields_120 := self.marc.get_fields("120"):
            if fields_120[0].get("a"):
                gender = None
                gender_type = fields_120[0]["a"]
                if gender_type == "a":
                    gender = "female"
                elif gender_type == "b":
                    gender = "male"
                elif gender_type == "-":
                    gender = "not known"
                if gender:
                    self.json_dict["gender"] = gender

    def trans_idref_language(self):
        """Transformation language 101 $a."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_language")
        if fields_101 := self.marc.get_fields("101"):
            if language_list := [
                language
                for language in fields_101[0].get_subfields("a")
                if language in LANGUAGES
            ]:
                self.json_dict["language"] = language_list

    def trans_idref_pid(self):
        """Transformation pid from field 001."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_pid")
        if fields_001 := self.marc.get_fields("001"):
            self.json_dict["pid"] = fields_001[0].data

    def trans_idref_identifier(self):
        """Transformation identifier from field 003."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_identifier")
        if fields_003 := self.marc.get_fields("003"):
            self.json_dict["identifier"] = fields_003[0].data
            identified_by = self.json_dict.get("identifiedBy", [])
            identified_by.append(
                {"source": "IDREF", "type": "uri", "value": fields_003[0].data}
            )
            self.json_dict["identifiedBy"] = identified_by

    def trans_idref_birth_and_death_dates(self):
        """Transformation birth_date and death_date."""

        def format_103_date(date_str):
            """Format date from 103.."""
            date = ""
            if date_str := date_str.strip().replace(" ", ""):
                unknown = False
                if date_str[-1] == "?":
                    unknown = True
                    date_str = date_str[:-1]
                year = date_str[:4]
                month = date_str[4:6]
                day = date_str[6:8]
                if year:
                    date = year
                if month:
                    date += f"-{month}"
                if day:
                    date += f"-{day}"
                if unknown:
                    date += "?"
            return date or None

        def format_200_date(date_str):
            """Format date from 200.."""
            date_formated = date_str.replace(" ", "")
            if date_formated == "....":
                return None
            return date_formated

        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_birth_and_death_dates")
        birth_date = ""
        death_date = ""
        if fields_103 := self.marc.get_fields("103"):
            if fields_103[0].get("a"):
                birth_date = format_103_date(fields_103[0]["a"])
            if fields_103[0].get("b"):
                death_date = format_103_date(fields_103[0]["b"])
        elif fields_200 := self.marc.get_fields("200"):
            if fields_200[0].get("f"):
                dates = fields_200[0]["f"].split("-")
                birth_date = format_200_date(dates[0])
                if len(dates) > 1:
                    death_date = format_200_date(dates[1])

        start_date_name = "date_of_birth"
        end_date_name = "date_of_death"
        if self.marc.get_fields("210"):
            start_date_name = "date_of_establishment"
            end_date_name = "date_of_termination"
        if birth_date:
            self.json_dict[start_date_name] = birth_date
        if death_date:
            self.json_dict[end_date_name] = death_date

    def trans_idref_biographical_information(self):
        """Transformation biographical_information 300 $a 34x $a."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_biographical_information")
        tag_list = [300] + list(range(340, 349 + 1))  # 300, 340:349
        biographical_information = []
        subfields = {"a": ", "}
        for tag in tag_list:
            biographical_information += build_string_list_from_fields(
                self.marc, str(tag), subfields
            )
        if biographical_information:
            self.json_dict["biographical_information"] = biographical_information

    def trans_idref_numeration(self):
        """Transformation numeration 200 $d."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_numeration")
        subfields = {"d": " "}
        numeration = build_string_list_from_fields(self.marc, "200", subfields)
        if numeration and numeration[0]:
            self.json_dict["numeration"] = numeration[0]

    def trans_idref_qualifier(self):
        """Transformation qualifier 200 $c."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_qualifier")
        subfields = {"c": " "}
        qualifier = build_string_list_from_fields(self.marc, "200", subfields)
        if qualifier and qualifier[0]:
            self.json_dict["qualifier"] = qualifier[0]

    def trans_idref_preferred_name(self):
        """Transformation preferred_name 200/210."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_preferred_name")
        tag = "200"
        subfields = {"a": ", ", "b": ", ", "c": ", "}
        tag_grouping = []
        if self.marc.get_fields("210"):
            tag = "210"
            subfields = {"a": ", ", "b": ". ", "c": ", "}
            tag_grouping = [
                {
                    "subtags": "c",
                    "start": " (",
                    "end": ")",
                    "delimiter": "",
                    "subdelimiter": ", ",
                }
            ]
        variant_names = self.json_dict.get("variant_name", [])
        preferred_names = build_language_string_list_from_fields(
            record=self.marc, tag=tag, subfields=subfields, tag_grouping=tag_grouping
        )
        for preferred_name in preferred_names:
            if self.json_dict.get("preferred_name"):
                variant_names.append(preferred_name)
            else:
                self.json_dict["preferred_name"] = preferred_name

        if variant_names:
            self.json_dict["variant_name"] = variant_names

    def trans_idref_authorized_access_point(self):
        """Transformation authorized_access_point. 200/210."""
        tag = "200"
        agent = "bf:Person"
        subfields = {
            "a": ", ",
            "b": ", ",
            "c": ", ",
            "d": ", ",
            "f": ", ",
            "x": " - - ",
        }
        tag_grouping = []
        if self.marc.get_fields("210"):
            tag = "210"
            agent = "bf:Organisation"
            self.json_dict["conference"] = self.marc["210"].indicators[0] == "1"
            subfields = {
                "a": ", ",
                "b": ". ",
                "c": ", ",
                "d": " ; ",
                "e": " ; ",
                "f": " ; ",
                "x": " - -",
            }
            tag_grouping = [
                {
                    "subtags": "c",
                    "start": " (",
                    "end": ")",
                    "delimiter": "",
                    "subdelimiter": ", ",
                },
                {
                    "subtags": "def",
                    "start": " (",
                    "end": ")",
                    "delimiter": "",
                    "subdelimiter": " ; ",
                },
            ]

        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_authorized_access_point")
        variant_access_points = self.json_dict.get("variant_access_point", [])
        authorized_access_points = build_language_string_list_from_fields(
            record=self.marc, tag=tag, subfields=subfields, tag_grouping=tag_grouping
        )
        for authorized_access_point in authorized_access_points:
            self.json_dict["type"] = agent
            if self.json_dict.get("authorized_access_point"):
                variant_access_points.append(authorized_access_point)
            else:
                self.json_dict["authorized_access_point"] = authorized_access_point
        if variant_access_points:
            self.json_dict["variant_access_point"] = variant_access_points

    def trans_idref_variant_name(self):
        """Transformation variant_name 400/410."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_variant_name")
        tag = "400"
        subfields = {"a": ", ", "b": ", ", "c": ", "}
        tag_grouping = []
        if self.marc.get_fields("410"):
            tag = "410"
            subfields = {"a": ", ", "b": ". ", "c": ", "}
            tag_grouping = [
                {
                    "subtags": "c",
                    "start": " (",
                    "end": ")",
                    "delimiter": "",
                    "subdelimiter": ", ",
                }
            ]
        variant_names = self.json_dict.get("variant_name", [])
        if variant_name := build_string_list_from_fields(
            record=self.marc, tag=tag, subfields=subfields, tag_grouping=tag_grouping
        ):
            variant_names += variant_name
        if variant_names:
            self.json_dict["variant_name"] = variant_names

    def trans_idref_variant_access_point(self):
        """Transformation variant_access_point 400/410."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_variant_access_point")
        tag = "400"
        subfields = {
            "a": ", ",
            "b": ", ",
            "c": ", ",
            "d": ", ",
            "f": ", ",
            "x": " - - ",
        }
        tag_grouping = []
        if self.marc.get_fields("410"):
            tag = "410"
            subfields = {
                "a": ", ",
                "b": ". ",
                "c": ", ",
                "d": " ; ",
                "e": " ; ",
                "f": " ; ",
                "x": " - - ",
            }
            tag_grouping = [
                {
                    "subtags": "c",
                    "start": " (",
                    "end": ")",
                    "delimiter": "",
                    "subdelimiter": ", ",
                },
                {
                    "subtags": "def",
                    "start": " (",
                    "end": ")",
                    "delimiter": "",
                    "subdelimiter": " ; ",
                },
            ]

        if variant_access_point := build_string_list_from_fields(
            record=self.marc, tag=tag, subfields=subfields, tag_grouping=tag_grouping
        ):
            self.json_dict["variant_access_point"] = variant_access_point

    def trans_idref_parallel_access_point(self):
        """Transformation parallel_access_point 700/710."""
        tag = "700"
        subfields = {
            "a": ", ",
            "b": ", ",
            "c": ", ",
            "d": ", ",
            "f": ", ",
            "x": " - - ",
        }
        tag_grouping = []
        if self.marc.get_fields("710"):
            tag = "710"
            subfields = {
                "a": ", ",
                "b": ". ",
                "c": ", ",
                "d": " ; ",
                "e": " ; ",
                "f": " ; ",
                "x": " - - ",
            }
            tag_grouping = [
                {
                    "subtags": "c",
                    "start": " (",
                    "end": ")",
                    "delimiter": "",
                    "subdelimiter": ", ",
                },
                {
                    "subtags": "def",
                    "start": " (",
                    "end": ")",
                    "delimiter": "",
                    "subdelimiter": " ; ",
                },
            ]

        if parallel_access_point := build_string_list_from_fields(
            record=self.marc, tag=tag, subfields=subfields, tag_grouping=tag_grouping
        ):
            self.json_dict["parallel_access_point"] = parallel_access_point

    def trans_idref_country_associated(self):
        """Transformation country_associated 102 $a codes ISO 3166-1."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", "trans_idref_country_associated")
        if fields_102 := self.marc.get_fields("102"):
            if fields_102[0].get("a"):
                country = COUNTRY_UNIMARC_MARC21.get(fields_102[0]["a"])
                if COUNTRIES.get(country):
                    self.json_dict["country_associated"] = country
