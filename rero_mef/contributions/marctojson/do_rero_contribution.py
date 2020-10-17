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

from rero_mef.contributions.marctojson.helper import \
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
        if self.marc.get_fields('100') \
                or self.marc.get_fields('110') \
                or self.marc.get_fields('111'):
            for func in dir(self):
                if func.startswith('trans'):
                    func = getattr(self, func)
                    func()

    @property
    def json(self):
        """Json data."""
        return self.json_dict or None

    def trans_rero_identifier(self):
        """Transformation identifier from field 035."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_rero_identifier')
        field_035 = self.marc['035']
        if field_035 and field_035['a']:
            pid = field_035['a']
            identifier = 'http://data.rero.ch/02-{pid}'.format(
                pid=pid)
            self.json_dict['pid'] = pid
            self.json_dict['identifier'] = identifier

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
                'Call Function', 'trans_rero_birth_and_death_dates')
        birth_date = ''
        death_date = ''
        field_100 = self.marc['100']
        if field_100:
            subfield_d = field_100['d']
            if subfield_d:
                dates_string = re.sub(r'\s+', ' ', subfield_d).strip()
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
                'Call Function', 'trans_rero_biographical_information')
        biographical_information = []
        subfields = {'a': ', '}
        for tag in [680]:
            biographical_information += \
                build_string_list_from_fields(self.marc, str(tag), subfields)
        if biographical_information:
            self.json_dict['biographical_information'] = \
                biographical_information

    def trans_rero_preferred_name(self):
        """Transformation preferred_name 100 $a."""
        tags = ['100']
        if self.marc.get_fields('110') or self.marc.get_fields('111'):
            tags = []
            if self.marc.get_fields('110'):
                tags.append('110')
            if self.marc.get_fields('111'):
                tags.append('111')
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_rero_preferred_name')
        subfields = {'a': ' '}
        variant_names = self.json_dict.get('variant_name', [])
        for tag in tags:
            preferred_names = build_string_list_from_fields(
                self.marc, tag, subfields)
            for preferred_name in preferred_names:
                if self.json_dict.get('preferred_name'):
                    variant_names.append(preferred_name)
                else:
                    self.json_dict['preferred_name'] = preferred_name
        if variant_names:
            self.json_dict['variant_name'] = variant_names

    def trans_rero_numeration(self):
        """Transformation numeration 100 $b."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_rero_numeration')
        subfields = {'b': ' '}
        numeration = build_string_list_from_fields(self.marc, '100', subfields)
        if numeration and numeration[0]:
            self.json_dict['numeration'] = numeration[0]

    def trans_rero_qualifier(self):
        """Transformation qualifier 100 $c."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_rero_qualifier')
        subfields = {'c': ' '}
        qualifier = build_string_list_from_fields(self.marc, '100', subfields)
        if qualifier and qualifier[0]:
            self.json_dict['qualifier'] = qualifier[0]

    def trans_rero_variant_name(self):
        """Transformation variant_name 400 $a."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_rero_variant_name')
        tag = '400'
        subfields = {'a': ', '}
        if self.marc.get_fields('410'):
            tag = '410'
        if self.marc.get_fields('411'):
            tag = '411'
        variant_names = self.json_dict.get('variant_name', [])
        variant_name = \
            build_string_list_from_fields(self.marc, tag, subfields)
        if variant_name:
            variant_names += variant_name
        if variant_names:
            self.json_dict['variant_name'] = variant_names

    def trans_rero_parallel_access_point(self):
        """Transformation variant_name 400 $a."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function', 'trans_rero_parallel_access_point')
        tag = '700'
        subfields = {'a': ', '}
        if self.marc.get_fields('710'):
            tag = '710'
        if self.marc.get_fields('711'):
            tag = '711'
        parallel_access_point = \
            build_string_list_from_fields(self.marc, tag, subfields)
        if parallel_access_point:
            self.json_dict['parallel_access_point'] = parallel_access_point

    def trans_rero_authorized_access_point(self):
        """Trans authorized_access_point 100 abcd."""
        tag = '100'
        agent = 'bf:Person'
        subfields = {'a': ', ', 'b': ', ', 'c': ', ', 'd': ', ', 'q': ', ',
                     'x': ' - '}
        if self.marc.get_fields('110'):
            tag = '110'
            agent = 'bf:Organisation'
            subfields = {'a': ', ', 'b': ', ', 'c': ', ', 'd': ', ', 'n': ', ',
                         'x': ' - '}
            self.json_dict['conference'] = False
        if self.marc.get_fields('111'):
            tag = '111'
            agent = 'bf:Organisation'
            subfields = {'a': ', ', 'b': ', ', 'c': ', ', 'd': ', ', 'n': ', ',
                         'x': ' - '}
            self.json_dict['conference'] = True
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function', 'trans_rero_authorized_access_point')
        self.json_dict['bf:Agent'] = agent
        authorized_access_points = \
            build_string_list_from_fields(self.marc, tag, subfields)
        variant_access_points = self.json_dict.get('variant_access_point', [])
        for authorized_access_point in authorized_access_points:
            if self.json_dict.get('authorized_access_point'):
                variant_access_points.append(authorized_access_point)
            else:
                self.json_dict['authorized_access_point'] = \
                    authorized_access_point
        if variant_access_points:
            self.json_dict['variant_access_point'] = variant_access_points

    def trans_gnd_variant_access_point(self):
        """Transformation variant_access_point 410/411 $abc."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function', 'trans_gnd_variant_access_point'
            )
        tag = '400'
        subfields = {'a': ', ', 'b': ', ', 'c': ', ', 'd': ', ', 'q': ', ',
                     'x': ' - '}
        if self.marc.get_fields('410'):
            tag = '410'
            subfields = {'a': ', ', 'b': ', ', 'c': ', ', 'd': ', ', 'n': ', ',
                         'x': ' - '}
        if self.marc.get_fields('411'):
            tag = '411'
            subfields = {'a': ', ', 'b': ', ', 'c': ', ', 'd': ', ', 'n': ', ',
                         'x': ' - '}
        variant_access_points = self.json_dict.get('variant_access_point', [])
        variant_access_point = \
            build_string_list_from_fields(self.marc, tag, subfields)
        if variant_access_point:
            variant_access_points += variant_access_point
        if variant_access_points:
            self.json_dict['variant_access_point'] = variant_access_points
