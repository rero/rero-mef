# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Marctojsons transformer for RERO records."""

import re

from rero_mef.marctojson.helper import build_string_list_from_fields


class Transformation:
    """Transformation MARC21 to JSON for RERO autority person."""

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
        if (
            self.marc.get_fields("100")
            or self.marc.get_fields("110")
            or self.marc.get_fields("111")
        ):
            for func in dir(self):
                if func.startswith("trans"):
                    func = getattr(self, func)
                    func()
        else:
            msg = "No 100 or 110 or 111"
            if self.logger and self.verbose:
                self.logger.warning(f"NO TRANSFORMATION: {msg}")
            self.json_dict = {"NO TRANSFORMATION": msg}
            self.trans_rero_identifier()

    @property
    def json(self):
        """Json data."""
        return self.json_dict or None

    def trans_rero_identifier(self):
        """Transformation identifier from field 035."""
        if self.logger and self.verbose:
            self.logger.info("Call Function: %s", "trans_rero_identifier")
        if fields_035 := self.marc.get_fields("035"):
            if fields_035[0].get("a"):
                pid = fields_035[0]["a"]
                identifier = f"http://data.rero.ch/02-{pid}"
                self.json_dict["pid"] = pid
                identified_by = self.json_dict.get("identifiedBy", [])
                identified_by.append(
                    {"source": "RERO", "type": "uri", "value": identifier}
                )
                self.json_dict["identifiedBy"] = identified_by

    def trans_rero_birth_and_death_dates(self):
        """Transformation birth_date and death_date.

        100 $d format: YYYY-YYYY (birth_date-death_date, split on hyphen)
        """
        # def format_100_date(date_str):
        #     """DocString."""
        #     date_formated = date_str
        #     if len(date_str) == 8:
        #         date_formated = \
        #             f'{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}'
        #     elif len(date_str) == 4:
        #         date_formated = date_str[0:4]
        #     return date_formated

        if self.logger and self.verbose:
            self.logger.info("Call Function: %s", "trans_rero_birth_and_death_dates")
        if fields_100 := self.marc.get_fields("100"):
            if fields_100[0].get("d"):
                dates_string = re.sub(r"\s+", " ", fields_100[0]["d"]).strip()
                dates = dates_string.split("-")
                birth_date = dates[0]
                # birth_date = format_100_date(dates[0])
                death_date = ""
                if len(dates) > 1:
                    death_date = dates[1]
                    # death_date = format_100_date(dates[1])
                if birth_date:
                    self.json_dict["date_of_birth"] = birth_date
                if death_date:
                    self.json_dict["date_of_death"] = death_date

    def trans_rero_biographical_information(self):
        """Transformation biographical_information 680 $a."""
        if self.logger and self.verbose:
            self.logger.info("Call Function: %s", "trans_rero_biographical_information")
        biographical_information = []
        subfields = {"a": ", "}
        for tag in [680]:
            biographical_information += build_string_list_from_fields(
                self.marc, str(tag), subfields
            )
        if biographical_information:
            self.json_dict["biographical_information"] = biographical_information

    def trans_rero_numeration(self):
        """Transformation numeration 100 $b."""
        if self.logger and self.verbose:
            self.logger.info("Call Function: %s", "trans_rero_numeration")
        subfields = {"b": " "}
        numeration = build_string_list_from_fields(self.marc, "100", subfields)
        if numeration and numeration[0]:
            self.json_dict["numeration"] = numeration[0]

    def trans_rero_qualifier(self):
        """Transformation qualifier 100 $c."""
        if self.logger and self.verbose:
            self.logger.info("Call Function: %s", "trans_rero_qualifier")
        subfields = {"c": " "}
        qualifier = build_string_list_from_fields(self.marc, "100", subfields)
        if qualifier and qualifier[0]:
            self.json_dict["qualifier"] = qualifier[0]

    def trans_rero_preferred_name(self):
        """Transformation preferred_name 100/110/111."""
        tag = "100"
        punctuation = ""
        spaced_punctuation = ""
        subfields = {"a": " ", "b": " ", "c": " "}
        if self.marc.get_fields("110") or self.marc.get_fields("111"):
            subfields = {"a": " ", "b": " ", "d": " "}
            if self.marc.get_fields("110"):
                tag = "110"
            if self.marc.get_fields("111"):
                tag = "111"
        if self.logger and self.verbose:
            self.logger.info("Call Function: %s", "trans_rero_preferred_name")
        variant_names = self.json_dict.get("variant_name", [])
        preferred_names = build_string_list_from_fields(
            record=self.marc,
            tag=tag,
            subfields=subfields,
            punctuation=punctuation,
            spaced_punctuation=spaced_punctuation,
        )
        for preferred_name in preferred_names:
            if self.json_dict.get("preferred_name"):
                variant_names.append(preferred_name)
            else:
                self.json_dict["preferred_name"] = preferred_name
        if variant_names:
            self.json_dict["variant_name"] = variant_names

    def trans_rero_authorized_access_point(self):
        """Trans authorized_access_point 100/110/111."""
        tag = "100"
        agent = "bf:Person"
        subfields = {"a": " ", "b": " ", "c": " ", "d": " ", "q": " ", "x": " "}
        punctuation = ""
        spaced_punctuation = ""
        if self.marc.get_fields("110") or self.marc.get_fields("111"):
            subfields = {
                "a": " ",
                "b": " ",
                "n": " ",
                "d": " ",
                "c": " ",
                "e": " ",
                "g": " ",
                "k": " ",
                "t": " ",
                "x": " ",
            }
            if self.marc.get_fields("110"):
                tag = "110"
                agent = "bf:Organisation"
                self.json_dict["conference"] = False
            if self.marc.get_fields("111"):
                tag = "111"
                agent = "bf:Organisation"
                self.json_dict["conference"] = True
        if self.logger and self.verbose:
            self.logger.info("Call Function: %s", "trans_rero_authorized_access_point")
        self.json_dict["type"] = agent
        authorized_access_points = build_string_list_from_fields(
            record=self.marc,
            tag=tag,
            subfields=subfields,
            punctuation=punctuation,
            spaced_punctuation=spaced_punctuation,
        )
        variant_access_points = self.json_dict.get("variant_access_point", [])
        for authorized_access_point in authorized_access_points:
            if self.json_dict.get("authorized_access_point"):
                variant_access_points.append(authorized_access_point)
            else:
                self.json_dict["authorized_access_point"] = authorized_access_point
        if variant_access_points:
            self.json_dict["variant_access_point"] = variant_access_points

    def trans_rero_variant_name(self):
        """Transformation variant_name 400/410/411."""
        if self.logger and self.verbose:
            self.logger.info("Call Function: %s", "trans_rero_variant_name")
        tag = "400"
        punctuation = ""
        spaced_punctuation = ""
        subfields = {"a": " ", "b": " ", "c": " "}
        # TODO: This code is not working for mixed tags!
        # Does 400, 410, 411 mixes exist?
        if self.marc.get_fields("410") or self.marc.get_fields("411"):
            subfields = {"a": " ", "b": " ", "d": " "}
            if self.marc.get_fields("410"):
                tag = "410"
            if self.marc.get_fields("411"):
                tag = "411"
        variant_names = self.json_dict.get("variant_name", [])
        if variant_name := build_string_list_from_fields(
            record=self.marc,
            tag=tag,
            subfields=subfields,
            punctuation=punctuation,
            spaced_punctuation=spaced_punctuation,
        ):
            variant_names += variant_name
        if variant_names:
            self.json_dict["variant_name"] = variant_names

    def trans_rero_variant_access_point(self):
        """Transformation variant_access_point 400/410/411."""
        if self.logger and self.verbose:
            self.logger.info("Call Function: %s", "trans_rero_variant_access_point")
        tag = "400"
        subfields = {"a": " ", "b": " ", "c": " ", "d": " ", "q": " ", "x": " "}
        punctuation = ""
        spaced_punctuation = ""
        if self.marc.get_fields("410") or self.marc.get_fields("411"):
            subfields = {
                "a": " ",
                "b": " ",
                "n": " ",
                "d": " ",
                "c": " ",
                "e": " ",
                "g": " ",
                "k": " ",
                "t": " ",
                "x": " ",
            }
            if self.marc.get_fields("410"):
                tag = "410"
            if self.marc.get_fields("411"):
                tag = "411"
        variant_access_points = self.json_dict.get("variant_access_point", [])
        if variant_access_point := build_string_list_from_fields(
            record=self.marc,
            tag=tag,
            subfields=subfields,
            punctuation=punctuation,
            spaced_punctuation=spaced_punctuation,
        ):
            variant_access_points += variant_access_point
        if variant_access_points:
            self.json_dict["variant_access_point"] = variant_access_points

    def trans_rero_parallel_access_point(self):
        """Transformation parallel_access_point 700/710/711."""
        if self.logger and self.verbose:
            self.logger.info("Call Function: %s", "trans_rero_parallel_access_point")
        tag = "700"
        subfields = {"a": " ", "b": " ", "c": " ", "d": " ", "q": " ", "x": " "}
        punctuation = ""
        spaced_punctuation = ""
        if self.marc.get_fields("710") or self.marc.get_fields("711"):
            subfields = {
                "a": " ",
                "b": " ",
                "n": " ",
                "d": " ",
                "c": " ",
                "e": " ",
                "g": " ",
                "k": " ",
                "t": " ",
                "x": " ",
            }
            if self.marc.get_fields("710"):
                tag = "710"
            if self.marc.get_fields("711"):
                tag = "711"
        if parallel_access_point := build_string_list_from_fields(
            record=self.marc,
            tag=tag,
            subfields=subfields,
            punctuation=punctuation,
            spaced_punctuation=spaced_punctuation,
        ):
            self.json_dict["parallel_access_point"] = parallel_access_point
