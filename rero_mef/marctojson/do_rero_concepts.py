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
"""Marctojsons transformer for RERO records."""

import contextlib

from rero_mef.marctojson.helper import build_string_list_from_fields


class Transformation(object):
    """Transformation MARC21 to JSON for RERO concept."""

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
        if self.marc.get_fields('150') or self.marc.get_fields('155'):
            for func in dir(self):
                if func.startswith('trans'):
                    func = getattr(self, func)
                    func()
        else:
            msg = 'No 150 or 155'
            if self.logger and self.verbose:
                self.logger.warning(f'NO TRANSFORMATION: {msg}')
            self.json_dict = {'NO TRANSFORMATION': msg}
            self.trans_rero_identifier()

    @property
    def json(self):
        """Json data."""
        return self.json_dict or None

    def trans_rero_identifier(self):
        """Transformation identifier from field 035."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_rero_identifier')
        identifiers = []
        field_035 = self.marc.get_fields('035')
        if field_035 and field_035[0].get('a'):
            self.json_dict['pid'] = field_035[0]['a']
            self.json_dict['type'] = 'bf:Topic'
            identifiers.append({
                'type': 'bf:Local',
                'source': 'RERO',
                'value': field_035[0]['a'].strip()
            })
        for field_016 in self.marc.get_fields('016'):
            identifiers.extend(
                {
                    'type': 'bf:Local',
                    'source': 'BNF',
                    'value': subfield_a.strip()
                }
                for subfield_a in field_016.get_subfields('a')
            )
        for field_679 in self.marc.get_fields('679'):
            identifiers.extend(
                {
                    'type': 'uri',
                    'value': subfield_u.strip()
                }
                for subfield_u in field_679.get_subfields('u')
            )
        if identifiers:
            self.json_dict['identifiedBy'] = identifiers

    def trans_rero_bnf_type(self):
        """Transformation bnf type from field 035."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_rero_bnf_type')
        with contextlib.suppress(Exception):
            if data_075_a := self.marc['075']['a'].strip():
                self.json_dict['bnf_type'] = data_075_a

    def trans_rero_authorized_access_point(self):
        """Transformation authorized_access_point from field 150 155."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function', 'trans_rero_authorized_access_point')
        tag = '155' if self.marc.get_fields('155') else '150'
        self.json_dict['authorized_access_point'] = self.marc[tag]['a'].strip()

    def trans_rero_variant_access_point(self):
        """Transformation variant_access_point from field 450 455."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function', 'trans_rero_variant_access_point')
        tag = '455' if self.marc.get_fields('455') else '450'
        subfields = {'a': ', ', 'x': ' - '}
        if variant_access_points := build_string_list_from_fields(
            self.marc, tag, subfields
        ):
            self.json_dict['variant_access_point'] = variant_access_points

    def trans_rero_relation(self):
        """Transformation broader related narrower 550 555."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_rero_relation')
        tag = '555' if self.marc.get_fields('555') else '550'
        relations = {}
        for field in self.marc.get_fields(tag):
            relation_type = 'related'
            if field.get('w'):
                if field['w'] == 'g':
                    relation_type = 'broader'
                elif field['w'] == 'h':
                    relation_type = 'narrower'
            relations.setdefault(relation_type, [])
            if field.get('0'):
                relations[relation_type].append({'$ref': field['0']})
            elif field.get('a'):
                relations[relation_type].append({
                    'authorized_access_point': field['a'].strip()
                })

        for relation, value in relations.items():
            if value:
                self.json_dict[relation] = value

    def trans_rero_classification(self):
        """Transformation classification from field 072."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_rero_classification')
        classifications = []
        for field_072 in self.marc.get_fields('072'):
            if field_072.get('a'):
                classification = field_072['a'].split('-')
                if len(classification) == 2:
                    classifications.append({
                        'type': 'bf:ClassificationDdc',
                        'classificationPortion': classification[0].strip(),
                        'name': classification[1].strip()
                    })

        if classifications:
            self.json_dict['classification'] = classifications

    def trans_rero_close_match(self):
        """Transformation closeMatch from field 682."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_rero_close_match')
        close_matchs = []
        for field_682 in self.marc.get_fields('682'):
            with contextlib.suppress(Exception):
                if field_682.get('a') and field_682.get('v'):
                    close_matchs.append({
                        'authorized_access_point': field_682['a'].strip(),
                        'source': field_682['v'].strip()
                    })
        if close_matchs:
            self.json_dict['closeMatch'] = close_matchs

    def trans_rero_note(self):
        """Transformation notes from field.

        670 $a: dataSource
        675 $a: dataNotFound
        680 __ $a: general
        667 $a: nonPublic
        260 _9 $a: seeReference
        260 __ $a: seeReference
        360 __ $a: seeAlsoReference
        016 $9: REROtreatment
        """
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_rero_note')
        notes = {
            'dataSource': [],
            'dataNotFound': [],
            'general': [],
            'nonPublic': [],
            'seeReference': [],
            'seeAlsoReference': [],
            'REROtreatment': [],
        }
        for field in self.marc.get_fields('670'):
            if field.get('a'):
                notes['dataSource'].append(field['a'].strip())
        for field in self.marc.get_fields('675'):
            if field.get('a'):
                notes['dataNotFound'].append(field['a'].strip())
        for field in self.marc.get_fields('680'):
            if field.get('a') and field.indicators == [' ', ' ']:
                notes['general'].append(field['a'].strip())
        for field in self.marc.get_fields('667'):
            if field.get('a'):
                notes['nonPublic'].append(field['a'].strip())
        for field in self.marc.get_fields('260'):
            if field.get('a') and field.indicators in [[' ', ' '], [' ', '9']]:
                notes['seeReference'].append(field['a'].strip())
        for field in self.marc.get_fields('360'):
            if field.get('a') and field.indicators == [' ', ' ']:
                notes['seeAlsoReference'].append(field['a'].strip())
        for field in self.marc.get_fields('016'):
            if field.get('9'):
                notes['REROtreatment'].append(field['9'].strip())
        for note, value in notes.items():
            if value:
                self.json_dict.setdefault('note', [])
                self.json_dict['note'].append({
                    'noteType': note,
                    'label': value
                })
