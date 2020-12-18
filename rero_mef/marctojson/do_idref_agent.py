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

"""Marctojsons transformer for Idref records."""

from datetime import datetime

import pytz

from rero_mef.marctojson.helper import COUNTRIES, COUNTRY_UNIMARC_MARC21, \
    LANGUAGE_SCRIPTS, LANGUAGES, build_string_list_from_fields, \
    remove_trailing_punctuation

LANGUAGE_SCRIPT_CODES = {
    'ba': 'latn',
    'ca': 'cyrl',
    'da': 'jpan',
    'db': 'jpan',
    'dc': 'jpan',
    'ea': 'hani',
    'fa': 'arab',
    'ga': 'grek',
    'ha': 'hebr',
    'ia': 'thai',
    'ja': 'deva',
    'ka': 'kore',
    'la': 'taml',
    'ma': 'geor',
    'mb': 'armn'
}


def get_language_script(field):
    """Get language script from $7 $8."""
    languages = {}
    if field['7'] or field['8']:
        for language_script in LANGUAGE_SCRIPTS:
            language, script_code = language_script.split('-')
            codes = languages.setdefault(language, {})
            codes[script_code] = 1
            languages[language] = codes
    try:
        subfield_8 = field['8']
        language = subfield_8[3:6]
        test = languages[language]
    except Exception as err:
        language = 'fre'
    try:
        subfield_7 = field['7']
        code = subfield_7[4:6]
        script_code = LANGUAGE_SCRIPT_CODES[code]
        test = languages[language][script_code]
    except Exception as err:
        script_code = 'latn'
    return '{language}-{script_code}'.format(
        language=language,
        script_code=script_code
    )


def build_language_string_list_from_fields(
        record, tag, subfields, punctuation=',', spaced_punctuation=':;/-',
        tag_grouping=[]):
    """Build a list of strings (one per field).

    from the given field tag and given subfields.
    the given separator is used as subfields delimiter.
    """
    fields = record.get_fields(tag)
    field_string_list = []
    for field in fields:
        grouping_data = []
        grouping_code = []
        for code, data in field:
            if code in subfields:
                if isinstance(data, (list, set)):
                    data = subfields[code].join(data)
                data = data.replace('\x98', '')
                data = data.replace('\x9C', '')
                data = data.replace(',,', ',')
                data = remove_trailing_punctuation(
                    data=data,
                    punctuation=punctuation,
                    spaced_punctuation=spaced_punctuation
                )
                data = data.strip()
                if data:
                    for group in tag_grouping:
                        if code in group['subtags']:
                            code = group['subtags']
                    if grouping_code and code == grouping_code[-1]:
                        grouping_data[-1].append(data)
                    else:
                        grouping_code.append(code)
                        grouping_data.append([data])
        subfield_string = ''
        for group in zip(grouping_code, grouping_data):
            grouping_start = ''
            grouping_end = ''
            delimiter = subfields.get(group[0])
            subdelimiter = subfields.get(group[0])
            for grouping in tag_grouping:
                if group[0] == grouping['subtags']:
                    grouping_start = grouping.get('start', '')
                    grouping_end = grouping.get('end', '')
                    delimiter = grouping.get('delimiter', '')
                    subdelimiter = grouping.get('subdelimiter', '')

            if subfield_string:
                subfield_string += delimiter + grouping_start + \
                    subdelimiter.join(group[1]) + grouping_end
            else:
                subfield_string = grouping_start + \
                    subdelimiter.join(group[1]) + grouping_end

        if subfield_string:
            language_script = get_language_script(field)
            if language_script == 'fre-latn':
                field_string_list.insert(0, subfield_string.strip())
            else:
                field_string_list.append(subfield_string.strip())
    return field_string_list


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
        if self.marc.get_fields('200') or self.marc.get_fields('210'):
            for func in dir(self):
                if func.startswith('trans'):
                    func = getattr(self, func)
                    func()

    @property
    def json(self):
        """Json data."""
        return self.json_dict or None

    def trans_idref_deleted(self):
        """Transformation deleted leader 5 == d."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_idref_deleted')
        if self.marc.leader[5] == 'd':
            self.json_dict['deleted'] = pytz.utc.localize(
                datetime.now()
            ).isoformat()

    def trans_idref_relation_pid(self):
        """Transformation old pids 035 $a $9 = sudoc."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_idref_relation_pid')
        fields_035 = self.marc.get_fields('035')
        for field_035 in fields_035:
            subfield_a = field_035['a']
            subfield_9 = field_035['9']
            if subfield_a and subfield_9 and subfield_9 == 'sudoc':
                self.json_dict['relation_pid'] = {
                    'value': subfield_a,
                    'type': 'redirect_from'
                }

    def trans_idref_gender(self):
        """Transformation gender 120 $a a:female, b: male, -:not known."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_idref_gender')
        gender = ""
        field_120 = self.marc['120']
        if field_120 and field_120['a']:
            gender_type = field_120['a']
            if gender_type == 'a':
                gender = 'female'
            elif gender_type == 'b':
                gender = 'male'
            elif gender_type == '-':
                gender = 'not known'
        if gender:
            self.json_dict['gender'] = gender

    def trans_idref_language(self):
        """Transformation language 101 $a."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_idref_language')
        field_101 = self.marc['101']
        language_list = []
        if field_101:
            for language in field_101.get_subfields('a'):
                if LANGUAGES.get(language):
                    language_list.append(language)
        if language_list:
            self.json_dict['language'] = language_list

    def trans_idref_pid(self):
        """Transformation pid from field 001."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_idref_pid')
        field_001 = self.marc['001']
        if field_001:
            self.json_dict['pid'] = field_001.data

    def trans_idref_identifier(self):
        """Transformation identifier from field 003."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_idref_identifier')
        field_003 = self.marc['003']
        if field_003:
            self.json_dict['identifier'] = field_003.data

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

        if self.logger and self.verbose:
            self.logger.info(
                'Call Function', 'trans_idref_birth_and_death_dates')
        birth_date = ''
        death_date = ''
        field_103 = self.marc['103']
        field_200 = self.marc['200']
        if field_103:
            if field_103['a']:
                birth_date = format_103_date(field_103['a'])
            if field_103['b']:
                death_date = format_103_date(field_103['b'])
        elif field_200 and field_200['f']:
            dates = field_200['f'].split('-')
            birth_date = format_200_date(dates[0])
            if len(dates) > 1:
                death_date = format_200_date(dates[1])

        start_date_name = 'date_of_birth'
        end_date_name = 'date_of_death'
        if self.marc.get_fields('210'):
            start_date_name = 'date_of_establishment'
            end_date_name = 'date_of_termination'
        if birth_date:
            self.json_dict[start_date_name] = birth_date
        if death_date:
            self.json_dict[end_date_name] = death_date

    def trans_idref_biographical_information(self):
        """Transformation biographical_information 300 $a 34x $a."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function', 'trans_idref_biographical_information')
        tag_list = [300] + list(range(340, 349 + 1))    # 300, 340:349
        biographical_information = []
        subfields = {'a': ', '}
        for tag in tag_list:
            biographical_information += \
                build_string_list_from_fields(self.marc, str(tag), subfields)
        if biographical_information:
            self.json_dict['biographical_information'] = \
                biographical_information

    def trans_idref_numeration(self):
        """Transformation numeration 200 $d."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_idref_numeration')
        subfields = {'d': ' '}
        numeration = build_string_list_from_fields(self.marc, '200', subfields)
        if numeration and numeration[0]:
            self.json_dict['numeration'] = numeration[0]

    def trans_idref_qualifier(self):
        """Transformation qualifier 200 $c."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_idref_qualifier')
        subfields = {'c': ' '}
        qualifier = build_string_list_from_fields(self.marc, '200', subfields)
        if qualifier and qualifier[0]:
            self.json_dict['qualifier'] = qualifier[0]

    def trans_idref_preferred_name(self):
        """Transformation preferred_name 200/210."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_idref_preferred_name')
        tag = '200'
        subfields = {'a': ', ', 'b': ', ', 'c': ', '}
        tag_grouping = []
        if self.marc.get_fields('210'):
            tag = '210'
            subfields = {'a': ', ', 'b': '. ', 'c': ', '}
            tag_grouping = [
                {
                    'subtags': 'c',
                    'start': ' ( ',
                    'end': ' )',
                    'delimiter': '',
                    'subdelimiter': ', '
                }
            ]
        variant_names = self.json_dict.get('variant_name', [])
        preferred_names = build_language_string_list_from_fields(
            record=self.marc,
            tag=tag,
            subfields=subfields,
            tag_grouping=tag_grouping
        )
        for preferred_name in preferred_names:
            if self.json_dict.get('preferred_name'):
                variant_names.append(preferred_name)
            else:
                self.json_dict['preferred_name'] = preferred_name

        if variant_names:
            self.json_dict['variant_name'] = variant_names

    def trans_idref_authorized_access_point(self):
        """Transformation authorized_access_point. 200/210."""
        tag = '200'
        agent = 'bf:Person'
        subfields = {'a': ', ', 'b': ', ', 'c': ', ', 'd': ', ', 'f': ', ',
                     'x': ' - - '}
        tag_grouping = []
        if self.marc.get_fields('210'):
            tag = '210'
            agent = 'bf:Organisation'
            self.json_dict['conference'] = self.marc['210'].indicators[0] == 1
            subfields = {'a': ', ', 'b': '. ', 'c': ', ', 'd': ' ; ',
                         'e': ' ; ', 'f': ' ; ', 'x': ' - -'}
            tag_grouping = [
                {
                    'subtags': 'c',
                    'start': ' ( ',
                    'end': ' )',
                    'delimiter': '',
                    'subdelimiter': ', '
                },
                {
                    'subtags': 'def',
                    'start': ' ( ',
                    'end': ' )',
                    'delimiter': '',
                    'subdelimiter': ' ; '
                }
            ]

        if self.logger and self.verbose:
            self.logger.info(
                'Call Function',
                'trans_authorized_access_point')
        variant_access_points = self.json_dict.get('variant_access_point', [])
        authorized_access_points = build_language_string_list_from_fields(
            record=self.marc,
            tag=tag,
            subfields=subfields,
            tag_grouping=tag_grouping
        )
        for authorized_access_point in authorized_access_points:
            self.json_dict['bf:Agent'] = agent
            if self.json_dict.get('authorized_access_point'):
                variant_access_points.append(authorized_access_point)
            else:
                self.json_dict['authorized_access_point'] = \
                    authorized_access_point
        if variant_access_points:
            self.json_dict['variant_access_point'] = variant_access_points

    def trans_idref_variant_name(self):
        """Transformation variant_name 400/410."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_idref_variant_name')
        tag = '400'
        subfields = {'a': ', ', 'b': ', ', 'c': ', '}
        tag_grouping = []
        if self.marc.get_fields('410'):
            tag = '410'
            subfields = {'a': ', ', 'b': '. ', 'c': ', '}
            tag_grouping = [
                {
                    'subtags': 'c',
                    'start': ' ( ',
                    'end': ' )',
                    'delimiter': '',
                    'subdelimiter': ', '
                }
            ]
        variant_names = self.json_dict.get('variant_name', [])
        variant_name = build_string_list_from_fields(
            record=self.marc,
            tag=tag,
            subfields=subfields,
            tag_grouping=tag_grouping
        )
        if variant_name:
            variant_names += variant_name
        if variant_names:
            self.json_dict['variant_name'] = variant_names

    def trans_idref_variant_access_point(self):
        """Transformation variant_access_point 400/410."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function', 'trans_idref_variant_access_point')
        tag = '400'
        subfields = {'a': ', ', 'b': ', ', 'c': ', ', 'd': ', ', 'f': ', ',
                     'x': ' - - '}
        tag_grouping = []
        if self.marc.get_fields('410'):
            tag = '410'
            subfields = {'a': ', ', 'b': '. ', 'c': ', ', 'd': ' ; ',
                         'e': ' ; ', 'f': ' ; ', 'x': ' - - '}
            tag_grouping = [
                {
                    'subtags': 'c',
                    'start': ' ( ',
                    'end': ' )',
                    'delimiter': '',
                    'subdelimiter': ', '
                },
                {
                    'subtags': 'def',
                    'start': ' ( ',
                    'end': ' )',
                    'delimiter': '',
                    'subdelimiter': ' ; '
                }
            ]

        variant_access_point = build_string_list_from_fields(
            record=self.marc,
            tag=tag,
            subfields=subfields,
            tag_grouping=tag_grouping
        )
        if variant_access_point:
            self.json_dict['variant_access_point'] = variant_access_point

    def trans_idref_parallel_access_point(self):
        """Transformation parallel_access_point 700/710."""
        tag = '700'
        subfields = {'a': ', ', 'b': ', ', 'c': ', ', 'd': ', ', 'f': ', ',
                     'x': ' - - '}
        tag_grouping = []
        if self.marc.get_fields('710'):
            tag = '710'
            subfields = {'a': ', ', 'b': '. ', 'c': ', ', 'd': ' ; ',
                         'e': ' ; ', 'f': ' ; ', 'x': ' - - '}
            tag_grouping = [
                {
                    'subtags': 'c',
                    'start': ' ( ',
                    'end': ' )',
                    'delimiter': '',
                    'subdelimiter': ', '
                },
                {
                    'subtags': 'def',
                    'start': ' ( ',
                    'end': ' )',
                    'delimiter': '',
                    'subdelimiter': ' ; '
                }
            ]

        parallel_access_point = build_string_list_from_fields(
            record=self.marc,
            tag=tag,
            subfields=subfields,
            tag_grouping=tag_grouping
        )
        if parallel_access_point:
            self.json_dict['parallel_access_point'] = parallel_access_point

    def trans_idref_country_associated(self):
        """Transformation country_associated 102 $a codes ISO 3166-1."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_idref_country_associated')
        field_102 = self.marc['102']
        if field_102:
            subfield_a = field_102['a']
            if subfield_a:
                country = COUNTRY_UNIMARC_MARC21.get(subfield_a)
                if COUNTRIES.get(country):
                    self.json_dict['country_associated'] = country
