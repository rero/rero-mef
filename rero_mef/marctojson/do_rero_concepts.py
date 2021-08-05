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


from rero_mef.marctojson.helper import build_string_list_from_fields


class Transformation(object):
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
        if self.marc.get_fields('150') or self.marc.get_fields('155'):
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
        identifiers = []
        field_035 = self.marc['035']
        if field_035 and field_035['a']:
            identifier = field_035['a']
            self.json_dict['pid'] = identifier
            identifiers.append({
                'type': 'bf:Local',
                'source': 'RERO',
                'value': identifier.strip()
            })
        for field_016 in self.marc.get_fields('016'):
            for subfield_a in field_016.get_subfields('a'):
                identifiers.append({
                    'type': 'bf:Local',
                    'source': 'BNF',
                    'value': subfield_a.strip()
                })
        for field_679 in self.marc.get_fields('679'):
            for subfield_u in field_679.get_subfields('u'):
                identifiers.append({
                    'type': 'uri',
                    'value': subfield_u.strip()
                })

        if identifiers:
            self.json_dict['identifiedBy'] = identifiers

    def trans_rero_bnf_type(self):
        """Transformation bnf type from field 035."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_rero_bnf_type')
        try:
            data_075_a = self.marc['075']['a'].strip()
            if data_075_a:
                self.json_dict['bnf_type'] = data_075_a
        except Exception as err:
            pass

    def trans_rero_authorized_access_point(self):
        """Transformation authorized_access_point from field 150 155."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function', 'trans_rero_authorized_access_point')
        tag = '150'
        if self.marc['155']:
            tag = '155'
        self.json_dict['authorized_access_point'] = self.marc[tag]['a'].strip()

    def trans_rero_variant_access_point(self):
        """Transformation variant_access_point from field 450 455."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function', 'trans_rero_variant_access_point')
        tag = '450'
        if self.marc['455']:
            tag = '455'
        subfields = {'a': ', ', 'x': ' - '}
        variant_access_points = build_string_list_from_fields(
            self.marc, tag, subfields)
        if variant_access_points:
            self.json_dict['variant_access_point'] = variant_access_points

    def trans_rero_relation(self):
        """Transformation broader related narrower 550 555."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_rero_relation')
        tag = '550'
        if self.marc['555']:
            tag = '555'
        relations = {}
        for field in self.marc.get_fields(tag):
            relation_type = 'related'
            subfield_w = field['w']
            if subfield_w:
                if subfield_w == 'g':
                    relation_type = 'broader'
                elif subfield_w == 'h':
                    relation_type = 'narrower'
            subfield_0 = field['0']
            relations.setdefault(relation_type, [])
            if subfield_0:
                relations[relation_type].append({
                    # TODO correct http
                    '$ref': subfield_0
                })
            else:
                subfield_a = field['a']
                if subfield_a:
                    relations[relation_type].append({
                        'authorized_access_point': subfield_a.strip()
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
            subfield_a = field_072['a']
            if subfield_a:
                classification = subfield_a.split('-')
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
        try:
            subfield_a = self.marc['682']['a']
            subfield_v = self.marc['682']['v']
            if subfield_a and subfield_v:
                self.json_dict['closeMatch'] = {
                    'authorized_access_point': subfield_a,
                    'source': subfield_v
                }
        except Exception as err:
            pass

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
            subfield_a = field['a']
            if subfield_a:
                notes['dataSource'].append(subfield_a.strip())
        for field in self.marc.get_fields('675'):
            subfield_a = field['a']
            if subfield_a:
                notes['dataNotFound'].append(subfield_a.strip())
        for field in self.marc.get_fields('680'):
            subfield_a = field['a']
            if subfield_a and field.indicators == [' ', ' ']:
                notes['general'].append(subfield_a.strip())
        for field in self.marc.get_fields('667'):
            subfield_a = field['a']
            if subfield_a:
                notes['nonPublic'].append(subfield_a.strip())
        for field in self.marc.get_fields('260'):
            subfield_a = field['a']
            if subfield_a and field.indicators in [[' ', ' '], [' ', '9']]:
                notes['seeReference'].append(subfield_a.strip())
        for field in self.marc.get_fields('360'):
            subfield_a = field['a']
            if subfield_a and field.indicators == [' ', ' ']:
                notes['seeAlsoReference'].append(subfield_a.strip())
        for field in self.marc.get_fields('016'):
            subfield_9 = field['9']
            if subfield_9:
                notes['REROtreatment'].append(subfield_9.strip())
        for note, value in notes.items():
            if value:
                self.json_dict.setdefault('note', [])
                self.json_dict['note'].append({
                    'noteType': note,
                    'label': value
                })
