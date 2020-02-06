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

"""Tasks used by  RERO-MEF."""

from io import StringIO

import click
from invenio_oaiharvester.api import get_info_by_oai_name
from pymarc.marcxml import parse_xml_to_array
from sickle import Sickle


def get_record(id, name, transformation, record_class, access_token=None,
               identifier=None, dbcommit=False, reindex=False, test_md5=False,
               verbose=False, **kwargs):
    """Get record from an OAI repo.

    :param identifier: identifier of record.
    """
    name = name
    url, metadata_prefix, lastrun, setspecs = get_info_by_oai_name(name)

    request = Sickle(url)

    params = {}
    if access_token:
        params['accessToken'] = access_token

    params['metadataPrefix'] = metadata_prefix
    setspecs = setspecs.split()
    params['identifier'] = '{identifier}{id}'.format(identifier=identifier,
                                                     id=id)
    try:
        record = request.GetRecord(**params)
    except Exception as err:
        return None, err
    records = parse_xml_to_array(StringIO(record.raw))
    rec = transformation(records[0]).json
    new_rec, action, mef_action = record_class.create_or_update(
        rec,
        dbcommit=dbcommit,
        reindex=reindex,
        test_md5=test_md5
    )
    if verbose:
        click.echo(
            'OAI-{name} get: {id} action: {action} {mef}'.format(
                name=name,
                id=id,
                action=action,
                mef=mef_action
            )
        )
    return new_rec, action, mef_action
