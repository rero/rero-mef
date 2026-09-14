# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test which refusals state that the source changed the record's type.

A record the source restated as a type we do not handle is deleted by the harvest; one that merely could not be
read is not. Only the first kind carries `UNSUPPORTED TYPE`.
"""

import pytest
from pymarc import Field, Record, Subfield

from rero_mef.marctojson.do_gnd_agent import Transformation as GndAgent
from rero_mef.marctojson.do_gnd_places import Transformation as GndPlace
from rero_mef.marctojson.do_idref_agent import Transformation as IdrefAgent
from rero_mef.marctojson.do_idref_concepts import Transformation as IdrefConcept

LEADER = "     nz  a22     o  4500"


def marc(fields, controls=()):
    record = Record(leader=LEADER)
    for tag, data in controls:
        record.add_ordered_field(Field(tag=tag, data=data))
    for tag, subs in fields:
        record.add_field(Field(tag=tag, indicators=[" ", " "], subfields=[Subfield(code=c, value=v) for c, v in subs]))
    return record


def test_idref_concept_of_an_unsupported_type_is_marked():
    """`Tu5` is a uniform title, not a Rameau subject."""
    data = IdrefConcept(marc=marc([], [("001", "1"), ("008", "Tu5")]), logger=None, verbose=False).json
    assert data["NO TRANSFORMATION"].startswith("008 not in")
    assert data["UNSUPPORTED TYPE"] is True


@pytest.mark.parametrize("status", ["Td3", "Td6", "Td9", "Td83", "Tf5", "Tz3"])
def test_a_rameau_subject_refused_for_its_status_is_not_marked(status):
    """`Td3`, `Td6`, `Td9`, `Td83` are Rameau subjects the gate refuses on status alone.

    They fire in the hundreds on a real harvest; taking them for a type change would delete them.
    """
    data = IdrefConcept(marc=marc([], [("001", "1"), ("008", status)]), logger=None, verbose=False).json
    assert data["NO TRANSFORMATION"].startswith("008 not in")
    assert "UNSUPPORTED TYPE" not in data


@pytest.mark.parametrize("code", ["Tu5", "Tg5", "Tp5", "Tb5", "Tq5", "Tl5"])
def test_types_we_do_not_model_are_marked(code):
    """A uniform title, a place or a person in the concept set really did stop being a concept."""
    data = IdrefConcept(marc=marc([], [("001", "1"), ("008", code)]), logger=None, verbose=False).json
    assert data["UNSUPPORTED TYPE"] is True


def test_idref_concept_that_could_not_be_read_is_not_marked():
    """No `008` states no type at all, so nothing is concluded from it."""
    data = IdrefConcept(marc=marc([], [("001", "1")]), logger=None, verbose=False).json
    assert data["NO TRANSFORMATION"] == "No 008"
    assert "UNSUPPORTED TYPE" not in data


def test_a_supported_idref_concept_is_transformed():
    """The gate lets a Rameau subject through."""
    data = IdrefConcept(
        marc=marc([("250", [("a", "Magnet")])], [("001", "1"), ("008", "Td5")]), logger=None, verbose=False
    ).json
    assert "NO TRANSFORMATION" not in data
    assert data["type"] == "bf:Topic"


def test_gnd_place_that_is_not_a_place_is_marked():
    """GND states the entity type in `075 $b` under `$2 gndgen`."""
    data = GndPlace(
        marc=marc([("075", [("b", "s"), ("2", "gndgen")])], [("001", "1")]), logger=None, verbose=False
    ).json
    assert data["NO TRANSFORMATION"] == "Not a place: bf:Topic"
    assert data["UNSUPPORTED TYPE"] is True


def test_gnd_agent_that_is_not_an_agent_is_marked():
    """A Sachbegriff is neither a person nor an organisation."""
    data = GndAgent(
        marc=marc([("075", [("b", "s"), ("2", "gndgen")])], [("001", "1")]), logger=None, verbose=False
    ).json
    assert data["NO TRANSFORMATION"].startswith("Not a person or organisation")
    assert data["UNSUPPORTED TYPE"] is True


def test_idref_agent_of_an_unsupported_type_is_marked():
    """An agent restated as a place states `Tg` and keeps no `200` or `210`."""
    record = marc([("215", [("a", "Fribourg")])], [("001", "1"), ("008", "Tg5")])
    data = IdrefAgent(marc=record, logger=None, verbose=False).json
    assert data["NO TRANSFORMATION"] == "No 200 or 210"
    assert data["UNSUPPORTED TYPE"] is True


@pytest.mark.parametrize("code", ["Tp5", "Tb5", "Tb7"])
def test_an_idref_agent_without_its_heading_field_is_not_marked(code):
    """A person or a corporate body that lost its heading field states no type change."""
    data = IdrefAgent(marc=marc([], [("001", "1"), ("008", code)]), logger=None, verbose=False).json
    assert data["NO TRANSFORMATION"] == "No 200 or 210"
    assert "UNSUPPORTED TYPE" not in data


def test_an_idref_agent_that_could_not_be_read_is_not_marked():
    """No `008` states no type at all, so nothing is concluded from it."""
    data = IdrefAgent(marc=marc([], [("001", "1")]), logger=None, verbose=False).json
    assert data["NO TRANSFORMATION"] == "No 200 or 210"
    assert "UNSUPPORTED TYPE" not in data


@pytest.mark.parametrize("transformation", [GndAgent, GndPlace])
def test_a_gnd_record_stating_no_type_is_not_marked(transformation):
    """No `075 $2 gndgen` states no type at all, so nothing is concluded from it."""
    data = transformation(marc=marc([("150", [("a", "Magnetismus")])], [("001", "1")]), logger=None, verbose=False).json
    assert data["NO TRANSFORMATION"].endswith("None")
    assert "UNSUPPORTED TYPE" not in data


@pytest.mark.parametrize("transformation", [GndAgent, GndPlace])
def test_a_gnd_record_stating_a_type_we_cannot_read_is_marked(transformation):
    """A code GND states but this list does not know is still a type it stated."""
    record = marc([("075", [("b", "zz"), ("2", "gndgen")])], [("001", "1")])
    data = transformation(marc=record, logger=None, verbose=False).json
    assert data["UNSUPPORTED TYPE"] is True


@pytest.mark.parametrize("transformation", [IdrefAgent, IdrefConcept])
@pytest.mark.parametrize("data", ["T", "", "Rameau", "T5"])
def test_an_idref_008_stating_no_readable_type_is_not_marked(transformation, data):
    """A truncated or unreadable `008` states no type, so the record is left alone."""
    record = marc([], [("001", "1"), ("008", data)])
    assert "UNSUPPORTED TYPE" not in transformation(marc=record, logger=None, verbose=False).json


@pytest.mark.parametrize("transformation", [GndAgent, GndPlace])
def test_a_gnd_type_stated_after_an_empty_field_is_read(transformation):
    """A `075 $2 gndgen` carrying no `$b` says nothing, so the next one is read."""
    record = marc(
        [("075", [("2", "gndgen")]), ("075", [("b", "s"), ("2", "gndgen")])],
        [("001", "1")],
    )
    data = transformation(marc=record, logger=None, verbose=False).json
    assert data["NO TRANSFORMATION"].endswith("bf:Topic")
    assert data["UNSUPPORTED TYPE"] is True
