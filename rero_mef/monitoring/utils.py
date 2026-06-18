# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Monitoring utilities."""

from sqlalchemy import text

DB_CONNECTION_COUNTS_QUERY = text(
    """
    select max_conn, used, res_for_super, max_conn-used-res_for_super res_for_normal from ( select count(*) used from
    pg_stat_activity ) t1, ( select setting::int res_for_super from pg_settings where
    name=$$superuser_reserved_connections$$ ) t2, ( select setting::int max_conn from pg_settings where
    name=$$max_connections$$ ) t3
        """
)


DB_CONNECTION_QUERY = text(
    """
    SELECT pid, application_name, client_addr, client_port, backend_start, xact_start, query_start,  wait_event, state,
    left(query, 64) FROM pg_stat_activity ORDER BY query_start DESC
    """
)
