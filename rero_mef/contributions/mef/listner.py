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
