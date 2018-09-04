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

"""Marctojsons transformer gnd."""

# ---------------------------- Modules ----------------------------------------
# import of standard modules

import re

from rero_mef.authorities.marctojson.helper import \
    build_string_list_from_fields


class Transformation(object):
    """Transformation unimarc to json for gnd autority person."""

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
            if func.startswith('trans'):
                func = getattr(self, func)
                func()

    @property
    def json(self):
        """Json data."""
        return self.json_dict

    def trans_gnd_gender(self):
        """Transform gender 375 $a 1 = male, 2 = female, " " = not known."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_gnd_gender')

        gender = ""
        fields_375 = self.marc.get_fields('375')
        if fields_375 and fields_375[0] and fields_375[0].get_subfields('a'):
            gender_type = fields_375[0].get_subfields('a')[0]
            if gender_type == '2':
                gender = 'female'
            elif gender_type == '1':
                gender = 'male'
            elif gender_type == ' ':
                gender = 'not known'
        if gender:
            self.json_dict['gender'] = gender

    def trans_gnd_language_of_person(self):
        """Transformation language_of_person 101 $a."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_gnd_language_of_person')
        fields_377 = self.marc.get_fields('377')
        language_list = []
        if fields_377 and fields_377[0] and fields_377[0].get_subfields('a'):
            for language in fields_377[0].get_subfields('a'):
                language_list.append(language)
        if language_list:
            self.json_dict['language_of_person'] = language_list

    def trans_gnd_identifier_for_person(self):
        """Transformation identifier_for_person from field 001."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function',
                'trans_gnd_identifier_for_person')
        fields_001 = self.marc.get_fields('001')
        if fields_001 and fields_001[0]:
            identifier_for_person = fields_001[0].data
            self.json_dict['identifier_for_person'] = identifier_for_person

    def trans_gnd_birth_and_death_dates(self):
        """Transformation birth_date and death_date."""
        def format_100_date(date_str):
            """DocString."""
            date_formated = date_str
            if len(date_str) == 8:
                date_formated = \
                    date_str[0:4] + '-' + date_str[4:6] + '-' + date_str[6:8]
            elif len(date_str) == 4:
                date_formated = date_str[0:4]
            return date_formated

        def format_548_date(date_str):
            """DocString."""
            date_formated = date_str
            if len(date_str) == 4:
                date_formated = date_str[0:4]
            return date_formated

        dates_per_tag = {}
        birth_date = ''
        death_date = ''
        fields_100 = self.marc.get_fields('100')
        if fields_100 and fields_100[0].get_subfields('d'):
            subfields_d = fields_100[0].get_subfields('d')
            dates_string = re.sub('\s+', ' ', subfields_d[0]).strip()
            dates = dates_string.split('-')
            birth_date = format_100_date(dates[0])
            dates_per_tag['100'] = {}
            dates_per_tag['100']['birth_date'] = format_100_date(dates[0])
            if len(dates) > 1:
                death_date = format_100_date(dates[1])
                dates_per_tag['100']['death_date'] = format_100_date(dates[1])

        fields_548 = self.marc.get_fields('548')
        for field_548 in fields_548:
            subfields_a = field_548.get_subfields('a')[0]
            subfields_4 = field_548.get_subfields('4')[0]
            if subfields_a and subfields_4:
                if subfields_4 in ('datl', 'datx'):
                    dates = subfields_a.split('-')
                    birth_date = format_548_date(dates[0])
                    dates_per_tag[subfields_4] = {}
                    dates_per_tag[subfields_4]['birth_date'] = birth_date
                    if len(dates) > 1:
                        death_date = format_548_date(dates[1])
                        dates_per_tag[subfields_4]['death_date'] = death_date
        result = {}
        if 'datx' in dates_per_tag:
            result = dates_per_tag['datx']
        elif 'datl' in dates_per_tag:
            result = dates_per_tag['datl']
        elif '100' in dates_per_tag:
            result = dates_per_tag['100']

        if 'birth_date' in result and result['birth_date']:
            self.json_dict['date_of_birth'] = result['birth_date']
        if 'death_date' in result and result['death_date']:
            self.json_dict['date_of_death'] = result['death_date']

    def trans_gnd_biographical_information(self):
        """Transformation biographical_information 670 $abu."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function',
                'trans_gnd_biographical_information')
        biographical_information = []
        for tag in [670]:
            biographical_information += \
                build_string_list_from_fields(self.marc, str(tag), 'abu', ', ')
        if biographical_information:
            self.json_dict['biographical_information'] = \
                biographical_information

    def trans_gnd_preferred_name_for_person(self):
        """Transformation preferred_name_for_person 100 $a."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function',
                'trans_preferred_name_for_person')
        preferred_name_for_person = \
            build_string_list_from_fields(self.marc, '100', 'a', ', ')
        if preferred_name_for_person:
            self.json_dict['preferred_name_for_person'] = \
                preferred_name_for_person[0]

    def trans_gnd_variant_name_for_person(self):
        """Transformation variant_name_for_person 400 $a."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function',
                'trans_gnd_variant_name_for_person')
        variant_name_for_person = \
            build_string_list_from_fields(self.marc, '400', 'a', ', ')
        if variant_name_for_person:
            self.json_dict['variant_name_for_person'] = variant_name_for_person

    def trans_gnd_authorized_access_point_representing_a_person(self):
        """Transformation authorized_access_point_representing_a_person.

        100 $abcdgt
        """
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function',
                'trans_gnd_authorized_access_point_representing_a_person')
        authorized_access_point_representing_a_person = \
            build_string_list_from_fields(self.marc, '100', 'abcdgt', ', ')
        if authorized_access_point_representing_a_person:
            self.json_dict['authorized_access_point_representing_a_person'] = \
                authorized_access_point_representing_a_person[0]

    def _trans_gnd_identifier_for_person_viaf(self):
        """Transformation identifier_for_person_viaf."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function',
                'trans_gnd_identifier_for_person_viaf')
        identifier_for_person_viaf = ''
        self.json_dict['identifier_for_person_viaf'] = \
            identifier_for_person_viaf
