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

"""Click command-line interface for MEF record management."""

from __future__ import absolute_import, print_function

import json
import sys

import click
from flask.cli import with_appcontext
from invenio_records.cli import records

from .authorities.api import BnfRecord, GndRecord, ReroRecord, ViafRecord
from .authorities.models import AgencyAction


@click.group()
def fixtures():
    """Fixtures management commands."""


@records.command()
@click.argument('agency')
@click.argument('source', type=click.File('r'), default=sys.stdin)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def create_or_update(agency, source, verbose):
    """Create or update authority person records."""
    agency_message = 'Update authority person records: {agency}'.format(
        agency=agency)
    click.secho(agency_message, fg='green')
    data = json.load(source)

    if isinstance(data, dict):
        data = [data]

    if agency == 'viaf':
        record_type = ViafRecord
    elif agency == 'bnf':
        record_type = BnfRecord
    elif agency == 'rero':
        record_type = ReroRecord
    elif agency == 'gnd':
        record_type = GndRecord
    for record in data:
            returned_record, status = record_type.create_or_update(
                record, agency=agency, dbcommit=True, reindex=True
            )
            if status != AgencyAction.DISCARD:
                id_type = ' record uuid: '
                id = returned_record.id
            else:
                id = record['identifier_for_person']
                id_type = ' record identifier_for_person : '

            message_str = {
                'agency': agency,
                'id_type': id_type,
                'id': id,
                'separator': ' | ',
                'status': status
            }
            message = '{agency}{id_type}{id}{separator}{status}'.format(
                **message_str)
            click.echo(message)


fixtures.add_command(create_or_update)
