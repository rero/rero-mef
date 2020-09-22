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

from celery import shared_task
from flask import current_app

from .mef.models import MefAction
from .models import AgencyAction
from .utils import get_agency_class
from .viaf.api import ViafRecord


@shared_task
def create_or_update(index, record, agency, dbcommit=True, reindex=True,
                     test_md5=False, verbose=False):
    """Create or update record task.

    :param index: index of record
    :param record: record data to use
    :param agency: agency to use
    :param dbcommit: db commit or not
    :param reindex: reindex or not
    :param test_md5: test md5 or not
    :param verbose: verbose or not
    :returns: id type, pid or id, agency action, mef action
    """
    agency_class = get_agency_class(agency)
    returned_record, agency_action, mef_action = agency_class.create_or_update(
        record, dbcommit=True, reindex=True, test_md5=test_md5
    )
    if agency_action != AgencyAction.DISCARD:
        id_type = 'uuid: '
        id = returned_record.id
    else:
        id_type = 'pid : '
        id = returned_record.get('pid')

    if verbose:
        message = '{index:<10} {agency} {type}{id:<38}' \
                  ' | {agency_action}\t| {mef_action}'.format(
                        index=index,
                        agency=agency,
                        type=id_type,
                        id=str(id),
                        agency_action=agency_action,
                        mef_action=mef_action
                    )
        current_app.logger.info(message)
    return id_type, str(id), str(agency_action), str(mef_action)


@shared_task
def delete(index, pid, agency, dbcommit=True, delindex=True, verbose=False):
    """Delete record task.

    :param index: index of record
    :param pid: pid to delete
    :param agency: agency to use
    :param dbcommit: db commit or not
    :param delindex: delete index or not
    :param verbose: verbose or not
    :returns: action
    """
    agency_class = get_agency_class(agency)
    agency_record = agency_class.get_record_by_pid(pid)
    action = None
    if agency_record:
        result, action = agency_record.delete(dbcommit=dbcommit,
                                              delindex=delindex)
        if verbose:
            message = '{index:<10} Deleted {agency} {pid:<38} {action}'.format(
                index=index,
                agency=agency,
                pid=pid,
                action=action
            )
            current_app.logger.info(message)
    else:
        message = '{index:<10} Not found {agency} {pid:<38}'.format(
            index=index,
            agency=agency,
            pid=pid,
        )
        current_app.logger.warning(message)
    return action


@shared_task
def create_mef_and_agencies_from_viaf(pid, dbcommit=True, reindex=True,
                                      test_md5=False, online=False,
                                      verbose=False):
    """Create MEF and agencies from VIAF task.

    :param pid: pid for viaf to use
    :param dbcommit: db commit or not
    :param reindex: reindex or not
    :param test_md5: test md5 or not
    :param online: get missing records from internet
    :param verbose: verbose or not
    :returns: string with pid and actions
    """
    viaf_record = ViafRecord.get_record_by_pid(pid)
    actions = viaf_record.create_mef_and_agencies(
        dbcommit=dbcommit,
        reindex=reindex,
        test_md5=test_md5,
        online=online,
        verbose=verbose
    )
    msgs = []
    for key, value in actions.items():
        if key == 'mef':
            msgs.insert(0, '{key}: {m_action}'.format(
                key=key,
                m_action=value
            ))
        else:
            if value['agency'] != AgencyAction.DISCARD and \
                    value['mef'] != MefAction.DISCARD:
                msgs.append('{key}: {a_action} {m_action}'.format(
                    key=key,
                    a_action=value['agency'],
                    m_action=value['mef']
                ))
    return ('Create MEF viaf pid:{pid} > {actions}'.format(
        pid=pid,
        actions=', '.join(msgs)
    ))


@shared_task
def create_mef_from_agency(pid, agency, dbcommit=True, reindex=True,
                           online=False):
    """Create MEF from agency task.

    :param pid: pid for agency to use
    :param agency: agency
    :param dbcommit: db commit or not
    :param reindex: reindex or not
    :param test_md5: test md5 or not
    :param online: get viaf online if not exist
    :returns: no return
    """
    agency_class = get_agency_class(agency)
    agency_record = agency_class.get_record_by_pid(pid)
    record, action, online = agency_record.create_or_update_mef_viaf_record(
        dbcommit=dbcommit,
        reindex=reindex,
        online=online
    )
    if not record:
        record = {}
    msg = 'Create MEF {agency} pid: {pid} > ' \
        'MEF pid: {mef_pid} {action} {online}'.format(
            agency=agency,
            pid=pid,
            mef_pid=record.get('pid'),
            action=action,
            online=online
        )
    return msg
