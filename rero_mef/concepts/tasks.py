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

"""Tasks used by RERO-MEF."""

from celery import shared_task

from ..utils import get_entity_class


@shared_task
def task_create_mef_for_concept(pid, concept, dbcommit=True, reindex=True,
                                online=False):
    """Create MEF from concept task.

    :param pid: pid for concept to use
    :param concept: concept
    :param dbcommit: db commit or not
    :param reindex: reindex or not
    :param online: get missing records from internet
    :returns: no return
    """
    concept_class = get_entity_class(concept)
    concept_record = concept_class.get_record_by_pid(pid)
    if concept_record:
        mef_record, mef_action, viaf_record, online = \
            concept_record.create_or_update_mef_viaf_record(
                dbcommit=dbcommit,
                reindex=reindex,
                online=online
            )
        mef_pid = 'Non'
        if mef_record:
            mef_pid = mef_record.pid
        msg = f'Create MEF from {concept} pid: {pid} ' \
            f'| mef: {mef_pid} {mef_action.value}'
        return msg
    else:
        return f'Not found concept {concept}:{pid}'
