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

"""Pytest helpers."""

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import os

from pymarc import marcxml

from rero_mef.authorities.marctojson.do_bnf_auth_person import \
    Transformation as Transformation_bnf
from rero_mef.authorities.marctojson.do_gnd_auth_person import \
    Transformation as Transformation_gnd
from rero_mef.authorities.marctojson.do_idref_auth_person import \
    Transformation as Transformation_idref
from rero_mef.authorities.marctojson.do_rero_auth_person import \
    Transformation as Transformation_rero


def trans_prep(source, xml_part_to_add):
    """Prepare transformation."""
    build_xml_record_file(xml_part_to_add)
    current_dir = os.path.dirname(__file__)
    file_name = os.path.join(
        current_dir, 'examples/xml_minimal_record.xml')
    records = marcxml.parse_xml_to_array(
        file_name, strict=False, normalize_form=None)
    trans = {
        'bnf': Transformation_bnf(marc=records[0], logger=None,
                                  verbose=False, transform=False),
        'gnd': Transformation_gnd(marc=records[0], logger=None,
                                  verbose=False, transform=False),
        'idref': Transformation_idref(marc=records[0], logger=None,
                                      verbose=False, transform=False),
        'rero': Transformation_rero(marc=records[0], logger=None,
                                    verbose=False, transform=False)
    }
    return trans.get(source)


def build_xml_record_file(xml_part_to_add):
    """Build_xml_record_file."""
    xml_record_as_text = """
        <record>
            <leader>00589nx  a2200193   45  </leader> """ + \
        xml_part_to_add + \
        '</record>'
    current_dir = os.path.dirname(__file__)
    file_name = os.path.join(
        current_dir, 'examples/xml_minimal_record.xml')
    with open(file_name, 'w', encoding='utf-8') as out:
        out.write(xml_record_as_text)
