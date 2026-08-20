# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test the BNF association identifier normalisation."""

import pytest

from rero_mef.concepts.utils import (
    bnf_ark_disagreements,
    bnf_ark_disagreements_by_match_type,
    bnf_association_identifier,
    bnf_association_identifiers,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # IdRef writes the number without check character.
        ("FRBNF11980468", "FRBNF11980468"),
        # GND and RERO keep the check character, digit or letter.
        ("FRBNF119308529", "FRBNF11930852"),
        ("FRBNF11930822X", "FRBNF11930822"),
        ("FRBNF177016487", "FRBNF17701648"),
        # The same number as a BNF ark uri, IdRef/RERO host and GND host.
        ("http://catalogue.bnf.fr/ark:/12148/cb119804687", "FRBNF11980468"),
        ("https://data.bnf.fr/ark:/12148/cb11930852x", "FRBNF11930852"),
        # Not a BNF number.
        ("FRBNF177105", None),
        ("(DE-101)1133622844", None),
        ("http://www.idref.fr/027851621", None),
        ("http://id.loc.gov/authorities/subjects/sh85042293", None),
        ("", None),
        (None, None),
    ],
)
def test_bnf_association_identifier(value, expected):
    """Normalise a BNF number or ark uri to `FRBNF` plus eight digits."""
    assert bnf_association_identifier(value) == expected


def test_bnf_association_identifiers_collapse_spellings():
    """Collapse the spellings of one number into a single identifier."""
    identified_by = [
        {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF119347860"},
        {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF11934786"},
        {"type": "uri", "value": "https://data.bnf.fr/ark:/12148/cb11934786x"},
        {"source": "GND", "type": "bf:Nbn", "value": "(DE-101)1133622844"},
    ]
    assert bnf_association_identifiers([identified_by]) == {"FRBNF11934786"}


def test_bnf_association_identifiers_keep_distinct_numbers():
    """Keep distinct BNF numbers apart so the caller can refuse to link."""
    identifiers = bnf_association_identifiers(
        [
            [{"source": "BNF", "type": "bf:Nbn", "value": "FRBNF11934786"}],
            [{"source": "BNF", "type": "bf:Nbn", "value": "FRBNF11934787"}],
        ]
    )
    assert identifiers == {"FRBNF11934786", "FRBNF11934787"}


def test_bnf_association_identifiers_ignore_an_agreeing_ark():
    """Only `bf:Nbn` identifies a record when the ark says the same thing."""
    identified_by = [
        {"source": "BNF", "type": "uri", "value": "http://catalogue.bnf.fr/ark:/12148/cb119329427"},
        {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF11932942"},
    ]
    assert bnf_association_identifiers([identified_by]) == {"FRBNF11932942"}


def test_bnf_association_identifiers_keep_the_bf_nbn_over_a_contradicting_ark():
    """The `bf:Nbn` is taken even when the ark names another BNF record."""
    identified_by = [
        {"source": "BNF", "type": "uri", "value": "http://catalogue.bnf.fr/ark:/12148/cb12072299t"},
        {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF11932942"},
    ]
    assert bnf_association_identifiers([identified_by]) == {"FRBNF11932942"}


def test_bnf_ark_disagreements_reports_a_contradicting_ark():
    """An ark naming another BNF record than the `bf:Nbn` is a source data error."""
    identified_by = [
        {"source": "BNF", "type": "uri", "value": "http://catalogue.bnf.fr/ark:/12148/cb12072299t"},
        {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF11932942"},
    ]
    assert bnf_ark_disagreements([identified_by]) == {"FRBNF12072299"}


def test_bnf_ark_disagreements_reports_a_number_only_the_ark_states():
    """A record whose number is only in an ark cannot be associated at all."""
    identified_by = [{"source": "BNF", "type": "uri", "value": "http://catalogue.bnf.fr/ark:/12148/cb180678592"}]
    assert bnf_ark_disagreements([identified_by]) == {"FRBNF18067859"}


def test_bnf_ark_disagreements_stays_quiet_when_the_ark_agrees():
    """The ark repeats the `bf:Nbn` on all but a few hundred records."""
    identified_by = [
        {"source": "BNF", "type": "uri", "value": "https://data.bnf.fr/ark:/12148/cb11934786x"},
        {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF119347860"},
    ]
    assert bnf_ark_disagreements([identified_by]) == set()


def test_bnf_ark_disagreements_by_match_type_audits_the_losing_match_type():
    """Report a closeMatch contradiction although the exactMatch decides the link.

    The association is read from `exactMatch` and never looks at `closeMatch`,
    but a `closeMatch` ark naming another BNF record is a source data error all
    the same, so auditing may not stop where the selection does.
    """
    record = {
        "exactMatch": [
            {
                "identifiedBy": [
                    {"source": "BNF", "type": "uri", "value": "https://data.bnf.fr/ark:/12148/cb11932942t"},
                    {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF11932942"},
                ]
            }
        ],
        "closeMatch": [
            {
                "identifiedBy": [
                    {"source": "BNF", "type": "uri", "value": "http://catalogue.bnf.fr/ark:/12148/cb15100021h"},
                    {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF12308292"},
                ]
            }
        ],
    }
    assert bnf_ark_disagreements_by_match_type(record) == {"closeMatch": {"FRBNF15100021"}}


def test_bnf_ark_disagreements_by_match_type_reports_each_match_type_apart():
    """Name the match type a contradicting ark sits in, so the source can be fixed."""

    def ark_only(value):
        """Build a match block stating a BNF number in an ark uri alone."""
        return [{"identifiedBy": [{"source": "BNF", "type": "uri", "value": value}]}]

    record = {
        "exactMatch": ark_only("http://catalogue.bnf.fr/ark:/12148/cb180678592"),
        "closeMatch": ark_only("http://catalogue.bnf.fr/ark:/12148/cb12072299t"),
    }
    assert bnf_ark_disagreements_by_match_type(record) == {
        "exactMatch": {"FRBNF18067859"},
        "closeMatch": {"FRBNF12072299"},
    }


def test_bnf_ark_disagreements_by_match_type_stays_quiet_when_every_ark_agrees():
    """A record whose arks all repeat their `bf:Nbn` reports nothing."""
    record = {
        "exactMatch": [
            {
                "identifiedBy": [
                    {"source": "BNF", "type": "uri", "value": "https://data.bnf.fr/ark:/12148/cb11934786x"},
                    {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF119347860"},
                ]
            }
        ],
        "closeMatch": [{"identifiedBy": [{"source": "GND", "type": "bf:Nbn", "value": "(DE-101)1133622844"}]}],
    }
    assert bnf_ark_disagreements_by_match_type(record) == {}


def test_bnf_ark_disagreements_by_match_type_handles_a_record_without_matches():
    """A record with no match block at all has nothing to contradict."""
    assert bnf_ark_disagreements_by_match_type({}) == {}
