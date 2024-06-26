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

"""Test cli."""

import tempfile
from os.path import dirname, isfile, join
from shutil import copy2

from click.testing import CliRunner

from rero_mef.agents.cli import create_csv_mef, create_csv_viaf


def test_create_csv_viaf_mef(script_info, tmpdir):
    """Test create CSV VIAF."""
    runner = CliRunner()
    viaf_text_file = join(dirname(__file__), "../../data/viaf.txt")
    output_directory = tempfile.mkdtemp()
    res = runner.invoke(
        create_csv_viaf, [viaf_text_file, output_directory], obj=script_info
    )
    assert res.output.strip().split("\n") == [
        "Create VIAF CSV files.",
        f"  VIAF input file: {viaf_text_file}",
        "  Number of VIAF records created: 859.",
    ]
    viaf_metadata = join(output_directory, "viaf_metadata.csv")
    viaf_pidstore = join(output_directory, "viaf_pidstore.csv")
    assert isfile(viaf_metadata)
    assert isfile(viaf_pidstore)
    with open(viaf_metadata) as in_file:
        metadata_count = 0
        for line in in_file:
            metadata_count += 1
        assert metadata_count == 859
        data = line.strip().split("\t")
        # don't use the first two lines with dates.
        assert data[3:] == [
            '{"bne_pid": "XX871391", '
            '"wiki": ['
            '"https://ar.wikipedia.org/wiki/\\\\u0642\\\\u0627\\\\u064a'
            '_\\\\u0633\\\\u062a\\\\u064a\\\\u0631\\\\u0646", '
            '"https://de.wikipedia.org/wiki/Guy_Stern", '
            '"https://en.wikipedia.org/wiki/Guy_Stern"'
            "], "
            '"rero_pid": "A003863577", '
            '"md5": "efbf1aaff7acc20e0a966432cfeeab12", '
            '"$schema": "https://mef.rero.ch/schemas/viaf/viaf-v0.0.1.json", '
            '"pid": "108685760"}',
            "1",
        ]
    with open(viaf_pidstore) as in_file:
        pidstore_count = sum(1 for _ in in_file)
        assert pidstore_count == metadata_count

    copy2(join(dirname(__file__), "../../data/aggnd_pidstore.csv"), output_directory)
    copy2(join(dirname(__file__), "../../data/aidref_pidstore.csv"), output_directory)
    copy2(join(dirname(__file__), "../../data/agrero_pidstore.csv"), output_directory)
    res = runner.invoke(
        create_csv_mef, [viaf_metadata, output_directory], obj=script_info
    )
    assert res.output.strip().split("\n") == [
        "Create MEF CSV files from VIAF metadata.",
        f"  VIAF input file: {viaf_metadata}",
        "  Number of MEF records created: 132.",
    ]
    mef_metadata = join(output_directory, "mef_metadata.csv")
    mef_pidstore = join(output_directory, "mef_pidstore.csv")
    mef_id = join(output_directory, "mef_id.csv")
    assert isfile(mef_metadata)
    assert isfile(mef_pidstore)
    assert isfile(mef_id)
