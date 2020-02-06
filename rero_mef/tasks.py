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

"""Celery tasks to index records."""

from celery import shared_task

from .authorities.api import AuthRecordIndexer


@shared_task(ignore_result=True)
def process_bulk_queue(version_type=None, es_bulk_kwargs=None):
    """Process bulk indexing queue.

    :param str version_type: Elasticsearch version type.
    :param dict es_bulk_kwargs: Passed to
        :func:`elasticsearch:elasticsearch.helpers.bulk`.
    Note: You can start multiple versions of this task.
    """
    AuthRecordIndexer(version_type=version_type).process_bulk_queue(
        es_bulk_kwargs=es_bulk_kwargs)


@shared_task(ignore_result=True)
def index_record(record_uuid):
    """Index a single record.

    :param record_uuid: The record UUID.
    """
    AuthRecordIndexer().index_by_id(record_uuid)


@shared_task(ignore_result=True)
def delete_record(record_uuid):
    """Delete a single record.

    :param record_uuid: The record UUID.
    """
    AuthRecordIndexer().delete_by_id(record_uuid)
