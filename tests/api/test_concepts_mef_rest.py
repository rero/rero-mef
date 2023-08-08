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

"""Test REST API MEF."""

import json
from datetime import datetime, timedelta, timezone

from flask import url_for
from utils import postdata

from rero_mef.concepts import ConceptMefRecord


def test_view_concepts_mef(client,
                           concept_rero_record, concept_mef_rero_record,
                           concept_mef_idref_redirect_record,
                           concept_idref_redirect_record):
    """Test concepts MEF."""
    pid = concept_mef_rero_record.get('pid')
    url = url_for('invenio_records_rest.comef_list')
    res = client.get(url)
    assert res.status_code == 200
    json_data = json.loads(res.get_data(as_text=True))
    assert json_data['hits']['total'] == 2
    assert json_data['aggregations'] == {
        'deleted': {'doc_count': 0},
        'deleted_entities': {'doc_count': 0},
        'sources': {
            'buckets': [{
                'doc_count': 1,
                'key': "idref"
            }, {
                'doc_count': 1,
                'key': "rero"
            }],
            'doc_count_error_upper_bound': 0,
            'sum_other_doc_count': 0
        },
        'type': {
            'buckets': [{
                'doc_count': 2,
                'key': 'bf:Topic'
            }],
            'doc_count_error_upper_bound': 0,
            'sum_other_doc_count': 0
        }
    }
    url = url_for('invenio_records_rest.comef_item', pid_value=pid)
    res = client.get(url)
    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    assert data.get('id') == pid
    assert data.get('metadata', {}).get('pid') == pid

    url = url_for('invenio_records_rest.comef_item', pid_value='WRONG')
    res = client.get(url, follow_redirects=True)
    assert res.status_code == 404
    assert json.loads(res.get_data(as_text=True)) == {
        "status": 404,
        "message": "PID does not exist."
    }


def test_concepts_mef_get_latest(client,
                                 concept_mef_rero_record, concept_rero_record,
                                 concept_mef_idref_record,
                                 concept_idref_record,
                                 concept_mef_idref_redirect_record,
                                 concept_idref_redirect_record):
    """Test concepts MEF get latest."""
    mef_data = concept_mef_rero_record.add_information(resolve=True)
    # No new record found
    assert ConceptMefRecord.get_latest(pid_type='rero', pid='XXX') == {}

    # New RERO record is old RERO record
    data = ConceptMefRecord.get_latest(pid_type='rero',
                                       pid=concept_rero_record.pid)
    data.pop('_created')
    data.pop('_updated')
    assert data == mef_data

    mef_data = concept_mef_idref_redirect_record.add_information(resolve=True)
    # New IdRef record is old IdRef record
    data = ConceptMefRecord.get_latest(pid_type='idref',
                                       pid=concept_idref_redirect_record.pid)
    data.pop('_created')
    data.pop('_updated')
    assert data == mef_data

    # New IdRef record is one redirect IdRef record
    # New IdRef record is one redirect IdRef record
    data = ConceptMefRecord.get_latest(pid_type='idref',
                                       pid=concept_idref_record.pid)
    data.pop('_created')
    data.pop('_updated')
    assert data == mef_data

    # test REST API
    url = url_for(
        'api_blueprint.concept_mef_get_latest',
        pid_type='idref',
        pid=concept_idref_record.pid
    )
    res = client.get(url)
    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    data.pop('_created')
    data.pop('_updated')
    assert data == mef_data


def test_concepts_mef_get_updated(client,
                                  concept_mef_rero_record, concept_rero_record,
                                  concept_mef_idref_record,
                                  concept_idref_record,
                                  concept_mef_idref_redirect_record,
                                  concept_idref_redirect_record):
    """Test concepts MEF get updated."""
    # New IdRef record is one redirect IdRef record
    res, data = postdata(
        client,
        'api_blueprint.concept_mef_get_updated',
        {}
    )
    assert res.status_code == 200
    pids = sorted([rec.get('pid') for rec in data])
    assert pids == ['1', '2', '3']

    res, data = postdata(
        client,
        'api_blueprint.concept_mef_get_updated',
        {"pids": ['2']}
    )
    assert res.status_code == 200
    pids = sorted([rec.get('pid') for rec in data])
    assert pids == ['2']

    res, data = postdata(
        client,
        'api_blueprint.concept_mef_get_updated',
        {"from_date": "2022-02-02"}
    )
    assert res.status_code == 200
    pids = sorted([rec.get('pid') for rec in data])
    assert pids == ['1', '2', '3']

    date = datetime.now(timezone.utc) + timedelta(days=1)
    res, data = postdata(
        client,
        'api_blueprint.concept_mef_get_updated',
        {"from_date": date.isoformat()}
    )
    assert res.status_code == 200
    pids = sorted([rec.get('pid') for rec in data])
    assert pids == []
