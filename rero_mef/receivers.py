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

"""Signals connections for RERO-MEF."""

from flask import current_app


def extend_mef_record(
    sender=None,
    json=None,
    record=None,
    index=None,
    doc_type=None,
    *args,
    **kwargs
):
    """Extend MEF record with list of sources."""
    mef_doc_type = current_app.config.get(
        'RECORDS_REST_ENDPOINTS', {}).get(
        'mef', {}
    ).get('search_type', '')
    if doc_type == mef_doc_type:
        sources = []
        # TODO: add the list of sources into the current_app.config
        if 'rero' in json:
            sources.append('rero')
        if 'gnd' in json:
            sources.append('gnd')
        if 'bnf' in json:
            sources.append('bnf')
        json['sources'] = sources
