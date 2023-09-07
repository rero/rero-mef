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

"""API for manipulating GND agent."""

from invenio_search.api import RecordsSearch

from .fetchers import gnd_id_fetcher
from .minters import gnd_id_minter
from .models import AgentGndMetadata
from .providers import AgentGndProvider
from ..api import AgentIndexer, AgentRecord


class AgentGndSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'agents_gnd'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class AgentGndRecord(AgentRecord):
    """Gnd agent class."""

    minter = gnd_id_minter
    fetcher = gnd_id_fetcher
    provider = AgentGndProvider
    name = 'gnd'
    viaf_pid_name = 'gnd_pid'
    viaf_source_code = 'DNB'
    model_cls = AgentGndMetadata
    search = AgentGndSearch

    @classmethod
    def get_online_record(cls, id_, debug=False):
        """Get online record.

        :param id: Id of online record.
        :param verbose: Verbosity.
        :returns: record or None
        """
        from .tasks import gnd_get_record
        return gnd_get_record(id_=id_, debug=debug)


class AgentGndIndexer(AgentIndexer):
    """Agent GND indexer."""

    record_cls = AgentGndRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(
            record_id_iterator,
            index=AgentGndSearch.Meta.index,
            doc_type='aggnd'
        )
