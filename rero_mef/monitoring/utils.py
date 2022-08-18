# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2022 RERO
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

"""Monitoring utilities."""


DB_CONNECTION_COUNTS_QUERY = """
        select
            max_conn, used, res_for_super,
            max_conn-used-res_for_super res_for_normal
        from
            (
                select count(*) used
                from pg_stat_activity
            ) t1,
            (
                select setting::int res_for_super
                from pg_settings
                where name=$$superuser_reserved_connections$$
            ) t2,
            (
                select setting::int max_conn
                from pg_settings
                where name=$$max_connections$$
            ) t3
        """


DB_CONNECTION_QUERY = """
        SELECT
            pid, application_name, client_addr, client_port, backend_start,
            xact_start, query_start,  wait_event, state, left(query, 64)
        FROM
            pg_stat_activity
        ORDER BY query_start DESC
    """
