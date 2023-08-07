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

"""Test monitoring."""

from click.testing import CliRunner

from rero_mef.agents.idref.api import AgentIdrefRecord
from rero_mef.monitoring.api import Monitoring
from rero_mef.monitoring.cli import es_db_counts_cli, es_db_missing_cli


def test_monitoring(app, agent_idref_data, script_info):
    """Test monitoring."""

    cli_output = [
        'DB - ES    type      count                      index   count_es',
        '----------------------------------------------------------------',
        '      0   aggnd          0                 agents_gnd          0',
        '      0  agrero          0                agents_rero          0',
        '      1  aidref          1               agents_idref          0',
        '      0  cidref          0             concepts_idref          0',
        '      0   comef          0               concepts_mef          0',
        '      0  corero          0              concepts_rero          0',
        '      0     mef          0                        mef          0',
        '      0  pidref          0               places_idref          0',
        '      0   plmef          0                 places_mef          0',
        '      0    viaf          0                       viaf          0'
    ]
    mon = Monitoring(time_delta=0)
    assert mon.get_es_count('xxx') == 'No >>xxx<< in ES'
    assert mon.get_db_count('xxx') == 'No >>xxx<< in DB'

    idref = AgentIdrefRecord.create(
        data=agent_idref_data,
        delete_pid=False,
        dbcommit=True,
        reindex=False
    )
    idref_pid = idref.pid
    assert mon.get_db_count('aidref') == 1
    assert mon.get_es_count('agents_idref') == 0
    assert mon.check() == {'aidref': {'db_es': 1}}
    assert mon.missing('aidref') == {
        'DB': [], 'ES': ['069774331'], 'ES duplicate': []}
    # not flushed by default
    assert mon.info() == {
        'aggnd': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'agents_gnd'},
        'agrero': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'agents_rero'},
        'aidref': {'db': 1, 'db-es': 1, 'es': 0, 'index': 'agents_idref'},
        'cidref': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'concepts_idref'},
        'comef': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'concepts_mef'},
        'corero': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'concepts_rero'},
        'mef': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'mef'},
        'pidref': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'places_idref'},
        'plmef': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'places_mef'},
        'viaf': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'viaf'}
    }
    assert mon.__str__().split('\n') == cli_output + ['']

    runner = CliRunner()
    res = runner.invoke(
        es_db_missing_cli, ['aidref', '-d', 0], obj=script_info)
    assert res.output == 'aidref: pids missing in ES:\n069774331\n'

    runner = CliRunner()
    res = runner.invoke(es_db_counts_cli, ['-m', '-d', 0], obj=script_info)
    assert res.output.split('\n') == cli_output + [
        'aidref: pids missing in ES:', '069774331', '']

    # we have to get the idref again because we lost the session after the use
    # of the CliRunner
    idref = AgentIdrefRecord.get_record_by_pid(idref_pid)
    idref.reindex()
    AgentIdrefRecord.flush_indexes()
    assert mon.get_es_count('agents_idref') == 1
    assert mon.check() == {}
    assert mon.missing('aidref') == {'DB': [], 'ES': [], 'ES duplicate': []}
    idref.delete(force=True, dbcommit=True)
    assert mon.get_db_count('aidref') == 0
    assert mon.get_es_count('agents_idref') == 1
    assert mon.check() == {'aidref': {'db_es': -1}}
    assert mon.missing('aidref') == {
        'DB': ['069774331'], 'ES': [], 'ES duplicate': []}
