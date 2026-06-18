# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test marctojson helper."""

from pymarc import Field, Record, Subfield

from rero_mef.marctojson.helper import build_string_list_from_fields


def test_build_string_list_from_fields():
    """Test build_string_list_from_fields."""
    record = Record()
    record.add_field(
        Field(
            tag="200",
            indicators=["0", "1"],
            subfields=[
                Subfield(code="a", value="Cerasi"),
                Subfield(code="b", value="Claudio et Elena"),
                Subfield(code="x", value="Collections d'art"),
            ],
        )
    )
    data = build_string_list_from_fields(
        record=record,
        tag="200",
        subfields={"a": ", ", "b": ", ", "c": ", ", "d": ", ", "f": ", ", "x": " - "},
    )
    assert data == ["Cerasi, Claudio et Elena - Collections d'art"]

    record = Record()
    record.add_field(
        Field(
            tag="210",
            indicators=["0", "1"],
            subfields=[
                Subfield(code="a", value="Place of public./distr."),
                Subfield(code="b", value="Address/publisher/dist."),
                Subfield(code="c", value="Name of publisher/dist."),
                Subfield(code="d", value="Date"),
                Subfield(code="e", value="Place"),
                Subfield(code="f", value="Address"),
            ],
        )
    )
    data = build_string_list_from_fields(
        record=record,
        tag="210",
        subfields={"a": ", ", "b": ". ", "c": ", ", "d": "; ", "e": "; ", "f": "; "},
        tag_grouping=[
            {
                "subtags": "c",
                "start": " (",
                "end": ")",
                "delimiter": "",
                "subdelimiter": ", ",
            },
            {
                "subtags": "def",
                "start": " (",
                "end": ")",
                "delimiter": "",
                "subdelimiter": "; ",
            },
        ],
    )
    assert data == [
        "Place of public./distr."
        ". Address/publisher/dist."
        " (Name of publisher/dist.)"
        " (Date; Place; Address)"
    ]
