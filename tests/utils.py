# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2021 RERO
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

"""Test utils."""

import json

from flask import url_for
from invenio_accounts.testutils import login_user_via_session


def create_record(cls, data, delete_pid=False):
    """Create a record in DB and index it."""
    record = cls.create(
        data=data,
        delete_pid=delete_pid,
        dbcommit=True,
        reindex=True
    )
    cls.flush_indexes()
    return record


def create_and_login_monitoring_user(app, client):
    """Creates and logins a monitoring user."""
    datastore = app.extensions['invenio-accounts'].datastore
    email = 'monitoring@rero.ch'
    user = datastore.get_user(email)
    if not user:
        user = datastore.create_user(
            email='monitoring@rero.ch',
            password='1234',
            active=True
        )
        role = datastore.create_role(
            name='monitoring', description='Monitoring Group')
        datastore.add_role_to_user(user, role)
        datastore.commit()
    login_user_via_session(client, user)
    return email


def get_json(response):
    """Get JSON from response."""
    return json.loads(response.get_data(as_text=True))


def postdata(
        client, endpoint, data=None, headers=None, url_data=None,
        force_data_as_json=True):
    """Build URL from given endpoint and send given data to it.

    :param force_data_as_json: the data sent forced json.
    :return: returns result and JSON from result.
    """
    if data is None:
        data = {}
    if headers is None:
        headers = [
            ('Accept', 'application/json'),
            ('Content-Type', 'application/json')
        ]
    if url_data is None:
        url_data = {}
    if force_data_as_json:
        data = json.dumps(data)
    res = client.post(
        url_for(endpoint, **url_data),
        data=data,
        headers=headers
    )
    output = get_json(res)
    return res, output
