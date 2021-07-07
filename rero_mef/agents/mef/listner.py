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

"""Signals connector for MEF records."""

from .api import MefSearch


def enrich_mef_data(sender, json=None, record=None, index=None, doc_type=None,
                    arguments=None, **kwargs):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    if index.split('-')[0] == MefSearch.Meta.index:
        sources = []
        if 'rero' in json:
            sources.append('rero')
            json['type'] = json['rero']['bf:Agent']
        if 'gnd' in json:
            sources.append('gnd')
            json['type'] = json['gnd']['bf:Agent']
        if 'idref' in json:
            sources.append('idref')
            json['type'] = json['idref']['bf:Agent']
        json['sources'] = sources
