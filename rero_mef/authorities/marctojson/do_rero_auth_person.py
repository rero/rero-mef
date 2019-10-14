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

"""Marctojsons transformer for Rero records."""


import re

from rero_mef.authorities.marctojson.helper import \
    build_string_list_from_fields


class Transformation(object):
    """Transformation marc21 to json for RERO autority person."""

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

    def trans_rero_identifier_for_person(self):
        """Transformation identifier_for_person from field 035."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function',
                'trans_rero_identifier_for_person')
        fields_035 = self.marc.get_fields('035')
        if fields_035 and fields_035[0].get_subfields('a'):
            pid = fields_035[0].get_subfields('a')[0]
            identifier_for_person = 'http://data.rero.ch/02-{pid}'.format(
                pid=pid)
            self.json_dict['pid'] = pid
            self.json_dict['identifier_for_person'] = identifier_for_person

    def trans_rero_birth_and_death_dates(self):
        """Transformation birth_date and death_date.

        100 $d pos. 1-4 YYYY birth_date
        100 $d pos. 6-9 YYYY birth_date
        """
        def format_100_date(date_str):
            """DocString."""
            date_formated = date_str
            if len(date_str) == 8:
                    date_data = {
                        'year': date_str[0:4],
                        'month': date_str[4:6],
                        'day': date_str[6:8]
                    }
                    date_formated = '{year}-{month}-{day}'.format(**date_data)
            elif len(date_str) == 4:
                date_formated = date_str[0:4]
            return date_formated

        if self.logger and self.verbose:
            self.logger.info(
                'Call Function',
                'trans_rero_birth_and_death_dates')
        birth_date = ''
        death_date = ''
        fields_100 = self.marc.get_fields('100')
        if fields_100 and fields_100[0].get_subfields('d'):
            subfields_d = fields_100[0].get_subfields('d')
            dates_string = re.sub(r'\s+', ' ', subfields_d[0]).strip()
            dates = dates_string.split('-')
            birth_date = dates[0]
            # birth_date = format_100_date(dates[0])
            if len(dates) > 1:
                death_date = dates[1]
                # death_date = format_100_date(dates[1])
        if birth_date:
            self.json_dict['date_of_birth'] = birth_date
        if death_date:
            self.json_dict['date_of_death'] = death_date

    def trans_rero_biographical_information(self):
        """Transformation biographical_information 680 $a."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function',
                'trans_rero_biographical_information')
        biographical_information = []
        for tag in [680]:
            biographical_information += \
                build_string_list_from_fields(self.marc, str(tag), 'a', ', ')
        if biographical_information:
            self.json_dict['biographical_information'] = \
                biographical_information

    def trans_rero_preferred_name_for_person(self):
        """Transformation preferred_name_for_person 100 $a."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function',
                'trans_rero_preferred_name_for_person')
        preferred_name_for_person = \
            build_string_list_from_fields(self.marc, '100', 'abc', ' ')
        if preferred_name_for_person:
            self.json_dict['preferred_name_for_person'] = \
                preferred_name_for_person[0]

    def trans_rero_variant_name_for_person(self):
        """Transformation variant_name_for_person 400 $a."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function',
                'trans_rero_variant_name_for_person')
        variant_name_for_person = \
            build_string_list_from_fields(self.marc, '400', 'a', ', ')
        if variant_name_for_person:
            self.json_dict['variant_name_for_person'] = variant_name_for_person

    def trans_rero_authorized_access_point_representing_a_person(self):
        """Trans authorized_access_point_representing_a_person 100 abcd."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function',
                'trans_rero_authorized_access_point_representing_a_person')
        authorized_access_point_representing_a_person = \
            build_string_list_from_fields(self.marc, '100', 'abcd', ', ')
        if authorized_access_point_representing_a_person:
            self.json_dict['authorized_access_point_representing_a_person'] = \
                authorized_access_point_representing_a_person[0]

    def _trans_rero_identifier_for_person_viaf(self):
        """Transformation identifier_for_person_viaf."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function',
                '_trans_rero_identifier_for_person_viaf')
        identifier_for_person_viaf = ''
        self.json_dict['identifier_for_person_viaf'] = \
            identifier_for_person_viaf
