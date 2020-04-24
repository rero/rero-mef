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

"""Marctojsons transformer for Bnf records."""

from rero_mef.authorities.marctojson.helper import \
    build_string_list_from_fields


class Transformation(object):
    """Transformation unimarc to json for idref autority person."""

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

    def trans_idref_gender(self):
        """Transformation gender 120 $a a:female, b: male, -:not known."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_gender')

        gender = ""
        fields_120 = self.marc.get_fields('120')
        if fields_120 and fields_120[0] and fields_120[0].get_subfields('a'):
            gender_type = fields_120[0].get_subfields('a')[0]
            if gender_type == 'a':
                gender = 'female'
            elif gender_type == 'b':
                gender = 'male'
            elif gender_type == '-':
                gender = 'not known'
        if gender:
            self.json_dict['gender'] = gender

    def trans_idref_language_of_person(self):
        """Transformation language_of_person 101 $a."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_language_of_person')
        fields_101 = self.marc.get_fields('101')
        language_list = []
        if fields_101 and fields_101[0] and fields_101[0].get_subfields('a'):
            for language in fields_101[0].get_subfields('a'):
                language_list.append(language)
        if language_list:
            self.json_dict['language_of_person'] = language_list

    def trans_pid(self):
        """Transformation pid from field 001."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_pid')
        fields_001 = self.marc.get_fields('001')
        if fields_001 and fields_001[0]:
            self.json_dict['pid'] = fields_001[0].data

    def trans_idref_identifier_for_person(self):
        """Transformation identifier_for_person from field 003."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_identifier_for_person')
        fields_003 = self.marc.get_fields('003')
        if fields_003 and fields_003[0]:
            self.json_dict['identifier_for_person'] = fields_003[0].data

    def trans_idref_birth_and_death_dates(self):
        """Transformation birth_date and death_date."""
        def format_103_date(date_str):
            """Format date from 103.."""
            date = ''
            date_str = date_str.strip().replace(' ', '')
            if date_str:
                unknown = False
                if date_str[-1] == '?':
                    unknown = True
                    date_str = date_str[:-1]
                year = date_str[0:4]
                month = date_str[4:6]
                day = date_str[6:8]
                if year:
                    date = year
                if month:
                    date += '-' + month
                if day:
                    date += '-' + day
                if unknown:
                    date += '?'
            return date or None

        def format_200_date(date_str):
            """Format date from 200.."""
            date_formated = date_str.replace(' ', '')
            if date_formated == '....':
                return None
            return date_formated

        birth_date = ''
        death_date = ''
        fields_103 = self.marc.get_fields('103')
        fields_200 = self.marc.get_fields('200')
        if fields_103:
            if fields_103[0].get_subfields('a'):
                subfields_a = fields_103[0].get_subfields('a')
                dates_string = subfields_a[0]
                birth_date = format_103_date(dates_string)
            if fields_103[0].get_subfields('b'):
                subfields_b = fields_103[0].get_subfields('b')
                dates_string = subfields_b[0]
                death_date = format_103_date(dates_string)
        elif fields_200 and fields_200[0].get_subfields('f'):
            subfields_f = fields_200[0].get_subfields('f')
            dates = subfields_f[0].split('-')
            birth_date = format_200_date(dates[0])
            if len(dates) > 1:
                death_date = format_200_date(dates[1])

        if birth_date:
            self.json_dict['date_of_birth'] = birth_date
        if death_date:
            self.json_dict['date_of_death'] = death_date

    def trans_idref_biographical_information(self):
        """Transformation biographical_information 300 $a 34x $a."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_biographical_information')
        tag_list = [300] + list(range(340, 349 + 1))    # 300, 340:349
        biographical_information = []
        subfields = {'a': ', '}
        for tag in tag_list:
            biographical_information += \
                build_string_list_from_fields(self.marc, str(tag), subfields)
        if biographical_information:
            self.json_dict['biographical_information'] = \
                biographical_information

    def trans_idref_preferred_name_for_person(self):
        """Transformation preferred_name_for_person 200 $a $b."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function',
                'trans_preferred_name_for_person')
        subfields = {'a': ', ', 'b': ', ', 'c': ', ', 'd': ' '}
        preferred_name_for_person = \
            build_string_list_from_fields(self.marc, '200', subfields)
        if preferred_name_for_person:
            self.json_dict['preferred_name_for_person'] = \
                preferred_name_for_person[0]

    def trans_idref_variant_name_for_person(self):
        """Transformation variant_name_for_person 400 $a $b."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_variant_name_for_person')
        subfields = {'a': ', ', 'b': ', '}
        variant_name_for_person = \
            build_string_list_from_fields(self.marc, '400', subfields)
        if variant_name_for_person:
            self.json_dict['variant_name_for_person'] = variant_name_for_person

    def trans_idref_authorized_access_point_representing_a_person(self):
        """Transformation authorized_access_point_representing_a_person.

        200 abcdf
        """
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function',
                'trans_authorized_access_point_representing_a_person')
        subfields = {'a': ', ', 'b': ', ', 'c': ', ', 'd': ', ', 'f': ', '}
        authorized_access_point_representing_a_person = \
            build_string_list_from_fields(self.marc, '200', subfields)
        if authorized_access_point_representing_a_person:
            self.json_dict['authorized_access_point_representing_a_person'] = \
                authorized_access_point_representing_a_person[0]

    def _trans_idref_identifier_for_person_viaf(self):
        """Transformation identifier_for_person_viaf."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function',
                'trans_identifier_for_person_viaf')
        identifier_for_person_viaf = ''
        self.json_dict['identifier_for_person_viaf'] = \
            identifier_for_person_viaf
