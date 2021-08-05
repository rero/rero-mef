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

from invenio_accounts.testutils import login_user_via_session


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
