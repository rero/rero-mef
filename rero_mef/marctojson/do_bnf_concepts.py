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
"""Marctojsons transformer for BNF records."""

import os
from datetime import datetime

import pytz
import requests
from flask import current_app

from rero_mef.concepts.rero.api import ConceptReroSearch
from rero_mef.marctojson.helper import build_string_list_from_fields
from rero_mef.utils import requests_retry_session


class Transformation(object):
    """Transformation BNF UNIMARC to JSON for RERO concepts."""

    def __init__(self, marc, logger=None, verbose=False, transform=True):
        """Constructor."""
        self.marc = marc
        self.logger = logger
        self.verbose = verbose
        self.json_dict = {}
        self.needs_tags = []
        self.needs_tags = ['216', '250', '280']
        if transform:
            self._transform()

    def get_rero_pid_local(self, bnf_id):
        """Find the RERO-MEF pid from bnf_id."""
        query = ConceptReroSearch() \
            .filter('term', identifiedBy__vale=bnf_id) \
            .filter('term', identifiedBy__type='bf:Local') \
            .filter('term', identifiedBy__source='BNF')
        for hit in query.source(['pid', 'identifiedBy']).scan():
            return hit.pid

    def get_rero_pid_remote(self, bnf_id):
        """Find the RERO-MEF pid from mef.rero.ch."""
        mef_host = os.environ.get('RERO_ILS_MEF_HOST', 'mef.rero.ch')
        path = 'api/concepts/rero'
        url = f'https://{mef_host}/{path}/?q=identifiedBy.value:{bnf_id}'
        # ' and identifiedBy.type:"bf:Local" and identifiedBy.source=BNF'
        response = requests_retry_session().get(url)
        status_code = response.status_code
        if status_code == requests.codes.ok:
            try:
                rero_pid = response.json()['hits']['hits'][0]['id']
                return rero_pid
            except Exception as err:
                # no pid found
                pass

    def _transform(self):
        """Call the transformation functions."""
        needs = ['216', '250', '280']
        if self.marc.get_fields(*self.needs_tags):
            for func in dir(self):
                if func.startswith('trans'):
                    func = getattr(self, func)
                    func()

    @property
    def json(self):
        """Json data."""
        return self.json_dict or None

    def trans_bnf_deleted(self):
        """Transformation deleted leader 5.

        leader 5 Record Status
        - c = corrected or revised record
        - d = deleted record
        - n = new record

        leader 9 Type of entity
        - a = personal name entry
        - b = corporate name entry
        - c = territorial or geographical name
        - d = trademark
        - e = family name
        - f = preferred title
        - g = collective preferred title
        - h = name/title
        - i = name/collective preferred title
        - j = topical subject
        - k = place access
        - l = form, genre or physical characteristics
        """
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_bnf_deleted')
        if self.marc.leader[5] == 'd':
            self.json_dict['deleted'] = pytz.utc.localize(
                datetime.now()
            ).isoformat()

    def trans_bnf_identifier(self):
        """Transformation identifier from field 001 003 009 035."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_bnf_identifier')

        identifiers = []
        for field_001 in self.marc.get_fields('001'):
            bnf_id = field_001.data.strip()
            pid = self.get_rero_pid_remote(bnf_id)
            if pid:
                self.json_dict['pid'] = pid
                identifiers.append({
                    'type': 'bf:Local',
                    'source': 'RERO',
                    'value': pid
                })
            else:
                # TODO: create new pid
                pass
            identifiers.append({
                'type': 'bf:Local',
                'source': 'BNF',
                'value': bnf_id
            })
        for field_003 in self.marc.get_fields('003'):
            identifiers.append({
                'type': 'uri',
                'value': field_003.data.strip()
            })
        for field_009 in self.marc.get_fields('009'):
            identifiers.append({
                'type': 'uri',
                'value': field_003.data.strip()
            })
        for field_035 in self.marc.get_fields('035'):
            subfield_a = field_035['a']
            if subfield_a:
                if subfield_a.startswith('(Sudoc)'):
                    identifiers.append({
                        'type': 'bf:Local',
                        'source': 'IDREF',
                        'value': subfield_a.replace('(Sudoc)', '')
                    })

        if identifiers:
            self.json_dict['identifiedBy'] = identifiers

    def trans_bnf_authorized_access_point(self):
        """Transformation authorized_access_point from field 216 250 280."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function', 'trans_bnf_authorized_access_point')
        tag = '216'
        if self.marc['250']:
            tag = '250'
        if self.marc['280']:
            tag = '280'
        self.json_dict['authorized_access_point'] = self.marc[tag]['a'].strip()

    def trans_bnf_variant_access_point(self):
        """Transformation variant_access_point from field 416 450 480."""
        if self.logger and self.verbose:
            self.logger.info(
                'Call Function', 'trans_bnf_variant_access_point')
        tag = '416'
        if self.marc['450']:
            tag = '450'
        if self.marc['480']:
            tag = '480'
        subfields = {'a': ', ', 'x': ' - '}
        variant_access_points = build_string_list_from_fields(
            self.marc, tag, subfields)
        if variant_access_points:
            self.json_dict['variant_access_point'] = variant_access_points

    def trans_bnf_relation(self):
        """Transformation broader related narrower 516 550 580."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_bnf_relation')
        tag = '516'
        if self.marc['550']:
            tag = '550'
        if self.marc['580']:
            tag = '580'
        relations = {}
        for field in self.marc.get_fields(tag):
            relation_type = 'related'
            subfield_5 = field['5']
            if subfield_5:
                if subfield_5 == 'g':
                    relation_type = 'broader'
                elif subfield_5 == 'h':
                    relation_type = 'narrower'
            subfield_3 = field['3']
            relations.setdefault(relation_type, [])
            rero_pid = None
            if subfield_3:
                rero_pid = self.get_rero_pid_remote(f'FRBNF{subfield_3}')
            if rero_pid:
                base_url = current_app.config.get('RERO_MEF_APP_BASE_URL')
                relations[relation_type].append({
                    '$ref': f'{base_url}/api/concepts/rero/{rero_pid}'
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

    def trans_bnf_classification(self):
        """Transformation classification from field 686."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_bnf_classification')
        classifications = []
        for field_686 in self.marc.get_fields('686'):
            subfield_a = field_686['a']
            subfield_c = field_686['c']
            if subfield_a and subfield_c:
                classifications.append({
                    'type': 'bf:ClassificationDdc',
                    'classificationPortion': subfield_a.strip(),
                    'name': subfield_c.strip()
                })
        if classifications:
            self.json_dict['classification'] = classifications

    def trans_bnf_close_match(self):
        """Transformation closeMatch from field 829."""
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_bnf_close_match')
        try:
            subfield_a = self.marc['829']['a']
            subfield_v = self.marc['829']['v']
            if subfield_a and subfield_v:
                self.json_dict['closeMatch'] = {
                    'authorized_access_point': subfield_a,
                    'source': subfield_v
                }
        except Exception as err:
            pass

    def trans_bnf_note(self):
        """Transformation notes from field.

        810 $a: dataSource
        815 $a: dataNotFound
        822 __ $a: general
        667 $a: nonPublic
        310 _9 $a: seeReference
        320 _9 $a: seeReference
        305 __ $a: seeAlsoReference
        """
        if self.logger and self.verbose:
            self.logger.info('Call Function', 'trans_bnf_note')
        notes = {
            'dataSource': [],
            'dataNotFound': [],
            'general': [],
            'nonPublic': [],
            'seeReference': [],
            'seeAlsoReference': [],
            'REROtreatment': [],
        }
        for field in self.marc.get_fields('810'):
            subfield_a = field['a']
            if subfield_a:
                notes['dataSource'].append(subfield_a.strip())
        for field in self.marc.get_fields('815'):
            subfield_a = field['a']
            if subfield_a:
                notes['dataNotFound'].append(subfield_a.strip())
        for field in self.marc.get_fields('822'):
            subfield_a = field['a']
            if subfield_a and field.indicators == [' ', ' ']:
                notes['general'].append(subfield_a.strip())
        # for field in self.marc.get_fields('667'):
        #     subfield_a = field['a']
        #     if subfield_a:
        #         notes['nonPublic'].append(subfield_a.strip())
        for field in self.marc.get_fields('310', '320'):
            subfield_a = field['a']
            if subfield_a and field.indicators in [[' ', ' '], [' ', '9']]:
                notes['seeReference'].append(subfield_a.strip())

        for field in self.marc.get_fields('305'):
            subfield_a = field['a']
            if subfield_a and field.indicators == [' ', ' ']:
                notes['seeAlsoReference'].append(subfield_a.strip())
        # for field in self.marc.get_fields('016'):
        #     subfield_9 = field['9']
        #     if subfield_9:
        #         notes['REROtreatment'].append(subfield_9.strip())
        for note, value in notes.items():
            if value:
                self.json_dict.setdefault('note', [])
                self.json_dict['note'].append({
                    'noteType': note,
                    'label': value
                })
