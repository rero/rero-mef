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

"""API for manipulating RERO agent."""

from invenio_search.api import RecordsSearch

from .fetchers import rero_id_fetcher
from .minters import rero_id_minter
from .models import AgentReroMetadata
from .providers import AgentReroProvider
from ..api import AgentIndexer, AgentRecord


class AgentReroSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'agents_rero'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class AgentReroRecord(AgentRecord):
    """Rero agent class."""

    minter = rero_id_minter
    fetcher = rero_id_fetcher
    provider = AgentReroProvider
    name = 'rero'
    viaf_source_code = 'RERO'
    viaf_pid_name = 'rero_pid'
    model_cls = AgentReroMetadata
    search = AgentReroSearch

    @classmethod
    def get_online_record(cls, id, debug=False):
        """Get online record."""
        from .tasks import rero_get_record
        return rero_get_record(id=id, debug=debug)


class AgentReroIndexer(AgentIndexer):
    """Agent RERO indexer."""

    record_cls = AgentReroRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(
            record_id_iterator,
            index=AgentReroSearch.Meta.index,
            doc_type='agrero'
        )
