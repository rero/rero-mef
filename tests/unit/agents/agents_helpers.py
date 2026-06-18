# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pytest helpers."""

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import os

from pymarc import marcxml

from rero_mef.marctojson.do_gnd_agent import Transformation as Transformation_gnd
from rero_mef.marctojson.do_idref_agent import Transformation as Transformation_idref
from rero_mef.marctojson.do_rero_agent import Transformation as Transformation_rero
from rero_mef.marctojson.logger import Logger


def trans_prep(source, xml_part_to_add):
    """Prepare transformation."""
    build_xml_record_file(xml_part_to_add)
    current_dir = os.path.dirname(__file__)
    file_name = os.path.join(current_dir, "examples/xml_minimal_record.xml")
    records = marcxml.parse_xml_to_array(file_name, strict=False, normalize_form=None)
    logger = Logger()
    trans = {
        "gnd": Transformation_gnd(
            marc=records[0], logger=logger, verbose=True, transform=False
        ),
        "idref": Transformation_idref(
            marc=records[0], logger=logger, verbose=True, transform=False
        ),
        "rero": Transformation_rero(
            marc=records[0], logger=logger, verbose=True, transform=False
        ),
    }
    return trans.get(source)


def build_xml_record_file(xml_part_to_add):
    """Build_xml_record_file."""
    xml_record_as_text = (
        """
        <record>
            <leader>00589nx  a2200193   45  </leader> """
        + xml_part_to_add
        + "</record>"
    )
    current_dir = os.path.dirname(__file__)
    file_name = os.path.join(current_dir, "examples/xml_minimal_record.xml")
    with open(file_name, "w", encoding="utf-8") as out:
        out.write(xml_record_as_text)
