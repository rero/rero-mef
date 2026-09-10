# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test concepts linking through the BNF number.

The fixtures used here are real records, taken from `data/corero.json`,
`data/cidref.json` and `data/cognd.json` or from https://mef.rero.ch/api/concepts.
They pin down which BNF numbers the three concept sources actually carry and
what MEF does with them today.
"""

from copy import deepcopy

from rero_mef.api import Action
from rero_mef.concepts import (
    ConceptGndRecord,
    ConceptIdrefRecord,
    ConceptMefRecord,
    ConceptReroRecord,
)
from rero_mef.concepts.utils import bnf_ark_disagreements


def _refs(mef_record):
    """Get the entity names referenced by a MEF record."""
    return {name for name in ConceptMefRecord.entities if name in mef_record}


def test_idref_gnd_link_via_close_match(app, concept_idref_link_data, concept_gnd_link_data):
    """Link IdRef and GND on the same BNF number, both written as `bf:Nbn`."""
    idref_record, _ = ConceptIdrefRecord.create_or_update(data=concept_idref_link_data, dbcommit=True, reindex=True)
    gnd_record, _ = ConceptGndRecord.create_or_update(data=concept_gnd_link_data, dbcommit=True, reindex=True)
    ConceptIdrefRecord.flush_indexes()
    ConceptGndRecord.flush_indexes()

    # Both sides compute the same association identifier.
    assert idref_record.association.identifiers == {"FRBNF12468269"}
    assert gnd_record.association.identifiers == {"FRBNF12468269"}

    # The association is found in both directions.
    assert idref_record.association_info["record"].pid == gnd_record.pid
    assert gnd_record.association_info["record"].pid == idref_record.pid

    mef_record, _ = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert _refs(mef_record) == {"idref", "gnd"}

    # One single MEF record holds both entities.
    assert len(ConceptMefRecord.get_mef(entity_name="idref", entity_pid=idref_record.pid)) == 1
    assert len(ConceptMefRecord.get_mef(entity_name="gnd", entity_pid=gnd_record.pid)) == 1


def test_gnd_check_char_bnf_number_is_normalised(app, concept_gnd_check_char_data):
    """Normalise a GND BNF number that keeps its check character."""
    gnd_record, _ = ConceptGndRecord.create_or_update(data=concept_gnd_check_char_data, dbcommit=True, reindex=True)
    ConceptGndRecord.flush_indexes()

    raw_values = [
        identified_by["value"]
        for match in gnd_record["exactMatch"]
        for identified_by in match["identifiedBy"]
        if identified_by.get("source") == "BNF"
    ]
    assert raw_values == ["FRBNF177016487"]
    assert gnd_record.association.identifiers == {"FRBNF17701648"}
    assert gnd_record.association.level == "exactMatch"


def test_gnd_bnf_number_spellings_are_one_identifier(app, concept_gnd_spellings_data, concept_idref_027269698_data):
    """Link when GND spells one BNF number several ways in one closeMatch.

    The three spellings used to count as three matches and disqualified the
    record; they now collapse into the single number IdRef carries.
    """
    idref_record, _ = ConceptIdrefRecord.create_or_update(
        data=concept_idref_027269698_data, dbcommit=True, reindex=True
    )
    gnd_record, _ = ConceptGndRecord.create_or_update(data=concept_gnd_spellings_data, dbcommit=True, reindex=True)
    ConceptIdrefRecord.flush_indexes()
    ConceptGndRecord.flush_indexes()

    assert gnd_record.association.identifiers == {"FRBNF11934786"}
    assert gnd_record.association.level == "closeMatch"
    assert idref_record.association.identifiers == {"FRBNF11934786"}

    mef_record, _ = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert _refs(mef_record) == {"idref", "gnd"}


def test_gnd_close_match_fan_out_is_not_linked(app, concept_idref_canon_data, concept_gnd_canon_data):
    """Refuse to link when several GND records close-match one BNF number.

    Sixteen camera models close-match `Canon (appareils-photo)`. None of them
    is the equivalent of the IdRef concept, so none may be picked.
    """
    idref_record, _ = ConceptIdrefRecord.create_or_update(data=concept_idref_canon_data, dbcommit=True, reindex=True)
    gnd_records = [
        ConceptGndRecord.create_or_update(data=data, dbcommit=True, reindex=True)[0] for data in concept_gnd_canon_data
    ]
    ConceptIdrefRecord.flush_indexes()
    ConceptGndRecord.flush_indexes()

    assert {identifier for record in gnd_records for identifier in record.association.identifiers} == {"FRBNF11931111"}
    assert idref_record.association_info["record"] is None
    for gnd_record in gnd_records:
        assert gnd_record.association_info["record"] is None

    mef_record, _ = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert _refs(mef_record) == {"idref"}


def test_gnd_close_match_becomes_ambiguous_and_unlinks_idref(
    app, concept_idref_027269698_data, concept_gnd_040048454_data
):
    """Remove an IdRef link when a GND closeMatch gains a second FRBNF."""
    idref_record, _ = ConceptIdrefRecord.create_or_update(
        data=concept_idref_027269698_data, dbcommit=True, reindex=True
    )
    gnd_record, _ = ConceptGndRecord.create_or_update(data=concept_gnd_040048454_data, dbcommit=True, reindex=True)
    ConceptIdrefRecord.flush_indexes()
    ConceptGndRecord.flush_indexes()

    mef_record, _ = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert mef_record.ref_pids.get("gnd") == gnd_record.pid

    ambiguous_data = deepcopy(concept_gnd_040048454_data)
    ambiguous_data["closeMatch"].append(
        {
            "authorized_access_point": "Another concept",
            "identifiedBy": [{"source": "BNF", "type": "bf:Nbn", "value": "FRBNF11934787"}],
            "source": "BNF",
        }
    )
    gnd_record, _ = ConceptGndRecord.create_or_update(data=ambiguous_data, dbcommit=True, reindex=True)
    ConceptGndRecord.flush_indexes()

    mef_record, _ = gnd_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert not gnd_record.association.identifiers
    assert mef_record.ref_pids.get("idref") is None
    assert ConceptMefRecord.get_mef(entity_name="idref", entity_pid=idref_record.pid)[0].ref_pids.get("gnd") is None


def test_gnd_exact_match_wins_over_close_match(app, concept_idref_canon_data, concept_gnd_canon_data):
    """Pick the single GND record asserting an exact match on the number."""
    idref_record, _ = ConceptIdrefRecord.create_or_update(data=concept_idref_canon_data, dbcommit=True, reindex=True)
    exact_data = deepcopy(concept_gnd_canon_data[2])
    exact_data["exactMatch"] = exact_data.pop("closeMatch")
    for data in [*concept_gnd_canon_data[:2], exact_data]:
        ConceptGndRecord.create_or_update(data=data, dbcommit=True, reindex=True)
    ConceptIdrefRecord.flush_indexes()
    ConceptGndRecord.flush_indexes()

    associated_record = idref_record.association_info["record"]
    assert associated_record.pid == exact_data["pid"]
    assert associated_record.association.level == "exactMatch"

    mef_record, _ = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert _refs(mef_record) == {"idref", "gnd"}
    assert mef_record["gnd"]["$ref"].endswith(f"/gnd/{exact_data['pid']}")


def test_rero_concept_carries_a_bnf_number_but_is_never_linked(app, concept_rero_link_data, concept_gnd_rero_link_data):
    """Leave RERO concepts unlinked although they carry the same BNF number.

    `ConceptReroRecord.association` states nothing, so the RERO record gets its
    own MEF record even though its BNF number is the GND one with the check
    character appended.
    """
    rero_record, _ = ConceptReroRecord.create_or_update(data=concept_rero_link_data, dbcommit=True, reindex=True)
    gnd_record, _ = ConceptGndRecord.create_or_update(data=concept_gnd_rero_link_data, dbcommit=True, reindex=True)
    ConceptReroRecord.flush_indexes()
    ConceptGndRecord.flush_indexes()

    # Same BNF number in both records, but RERO writes it as `bf:Local` and
    # keeps the check character.
    rero_bnf = next(
        identified_by["value"] for identified_by in rero_record["identifiedBy"] if identified_by["source"] == "BNF"
    )
    assert rero_bnf == "FRBNF119308529"
    assert gnd_record.association.identifiers == {"FRBNF11930852"}
    assert gnd_record.association.identifiers == {rero_bnf[:13]}

    # No identifier is computed for RERO, so no association is possible.
    assert not rero_record.association.identifiers
    assert rero_record.association_info["record"] is None
    assert rero_record.association_info["record_cls"] is None

    rero_mef_record, _ = rero_record.create_or_update_mef(dbcommit=True, reindex=True)
    gnd_mef_record, _ = gnd_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert _refs(rero_mef_record) == {"rero"}
    assert _refs(gnd_mef_record) == {"gnd"}
    assert rero_mef_record.pid != gnd_mef_record.pid


def test_duplicated_close_match_entries_link(app, concept_gnd_kochbuch_data, concept_idref_livres_cuisine_data):
    """Link when GND repeats the same closeMatch entry twice.

    GND `Kochbuch` holds `Livres de cuisine` twice, differing only by GND id.
    The two entries used to count as two matches and blocked the link.
    """
    gnd_record, _ = ConceptGndRecord.create_or_update(data=concept_gnd_kochbuch_data, dbcommit=True, reindex=True)
    idref_record, _ = ConceptIdrefRecord.create_or_update(
        data=concept_idref_livres_cuisine_data, dbcommit=True, reindex=True
    )
    ConceptGndRecord.flush_indexes()
    ConceptIdrefRecord.flush_indexes()

    assert gnd_record.association.identifiers == {"FRBNF12425736"}
    assert gnd_record.association.level == "closeMatch"
    assert idref_record.association.identifiers == {"FRBNF12425736"}

    mef_record, _ = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert _refs(mef_record) == {"idref", "gnd"}
    assert mef_record["gnd"]["$ref"].endswith("/gnd/041142403")


def test_exact_match_without_bnf_number_uses_close_match(app, concept_gnd_baum_data, concept_idref_027269698_data):
    """Link `Baum` to `Arbres` although the exactMatch entries hold no BNF number."""
    gnd_record, _ = ConceptGndRecord.create_or_update(data=concept_gnd_baum_data, dbcommit=True, reindex=True)
    idref_record, _ = ConceptIdrefRecord.create_or_update(
        data=concept_idref_027269698_data, dbcommit=True, reindex=True
    )
    ConceptGndRecord.flush_indexes()
    ConceptIdrefRecord.flush_indexes()

    assert gnd_record.association.identifiers == {"FRBNF11934786"}
    assert gnd_record.association.level == "closeMatch"

    mef_record, _ = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert _refs(mef_record) == {"idref", "gnd"}
    assert mef_record["gnd"]["$ref"].endswith("/gnd/040048454")


def test_conflicting_bnf_number_and_ark_follows_the_number(
    app, concept_gnd_sieg_data, concept_idref_victoire_data, concept_idref_epee_data
):
    """Follow the `bf:Nbn` when the BNF number and the BNF ark disagree.

    The `Victoire` closeMatch of GND `Sieg` carries a number pointing at IdRef
    `Épée (sport)` and an ark pointing at IdRef `Victoire`. The number decides,
    the ark is only reported, so `Sieg` links to `Épée (sport)`: the ark and the
    label of the closeMatch both say the number is the wrong one, which is a
    source data error to fix in GND rather than to guess around here.
    """
    gnd_record, _ = ConceptGndRecord.create_or_update(data=concept_gnd_sieg_data, dbcommit=True, reindex=True)
    victoire_record, _ = ConceptIdrefRecord.create_or_update(
        data=concept_idref_victoire_data, dbcommit=True, reindex=True
    )
    epee_record, _ = ConceptIdrefRecord.create_or_update(data=concept_idref_epee_data, dbcommit=True, reindex=True)
    ConceptGndRecord.flush_indexes()
    ConceptIdrefRecord.flush_indexes()

    assert victoire_record.association.identifiers == {"FRBNF15100021"}
    assert epee_record.association.identifiers == {"FRBNF12308292"}

    # The `bf:Nbn` decides; the contradicting ark is reported, not obeyed.
    assert gnd_record.association.identifiers == {"FRBNF12308292"}
    assert gnd_record.association.level == "closeMatch"
    assert bnf_ark_disagreements(match.get("identifiedBy", []) for match in gnd_record["closeMatch"]) == {
        "FRBNF15100021"
    }
    assert gnd_record.association_info["record"].pid == epee_record.pid

    mef_record, _ = epee_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert _refs(mef_record) == {"idref", "gnd"}
    mef_record, _ = victoire_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert _refs(mef_record) == {"idref"}


def test_rero_and_idref_share_the_bnf_ark(app, concept_rero_ark_data, concept_idref_ark_data):
    """Keep RERO and IdRef apart although IdRef holds the same BNF ark uri.

    RERO is frozen, so the link has to be computed from the IdRef side. IdRef
    carries no RERO pid, but it does carry the identical BNF ark uri, and the
    same BNF number once the prefix and the check character are dropped.
    """
    rero_record, _ = ConceptReroRecord.create_or_update(data=concept_rero_ark_data, dbcommit=True, reindex=True)
    idref_record, _ = ConceptIdrefRecord.create_or_update(data=concept_idref_ark_data, dbcommit=True, reindex=True)
    ConceptReroRecord.flush_indexes()
    ConceptIdrefRecord.flush_indexes()

    def arks(record):
        """Get the BNF ark uris of a record."""
        return {
            identified_by["value"]
            for identified_by in record["identifiedBy"]
            if "ark:/12148/" in identified_by["value"]
        }

    # The ark uri is identical, the BNF number needs normalising: RERO writes
    # `RERO119804685`, IdRef writes `FRBNF11980468`.
    assert arks(rero_record) == arks(idref_record) == {"http://catalogue.bnf.fr/ark:/12148/cb119804687"}
    assert idref_record.association.identifiers == {"FRBNF11980468"}
    assert not rero_record.association.identifiers

    # Nothing links them today: two MEF records for the same concept.
    rero_mef_record, _ = rero_record.create_or_update_mef(dbcommit=True, reindex=True)
    idref_mef_record, _ = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert rero_record["authorized_access_point"] == idref_record["authorized_access_point"]
    assert _refs(rero_mef_record) == {"rero"}
    assert _refs(idref_mef_record) == {"idref"}
    assert rero_mef_record.pid != idref_mef_record.pid


def test_rero_concept_mef_is_updated_in_place(app, concept_rero_link_data):
    """Update the MEF record of a source without association class.

    RERO has no association class, so the second call goes through the update
    branch of `create_or_update_mef` with no association name to look up.
    """
    rero_data = deepcopy(concept_rero_link_data)
    rero_data["pid"] = "A021001021_2"
    rero_record, _ = ConceptReroRecord.create_or_update(data=rero_data, dbcommit=True, reindex=True)
    ConceptReroRecord.flush_indexes()

    first_mef_record, actions = rero_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert actions == {first_mef_record.pid: Action.CREATE}

    second_mef_record, actions = rero_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert actions == {first_mef_record.pid: Action.REPLACE}
    assert second_mef_record.pid == first_mef_record.pid
    assert _refs(second_mef_record) == {"rero"}


def test_three_sources_end_in_two_mef_records(app, concept_rero_link_data, concept_gnd_rero_link_data):
    """Split three concepts sharing one BNF number over two MEF records.

    IdRef and GND are merged, RERO is left aside. A three-way link would need
    the BNF number of all three sources to be normalised into one key.
    """
    idref_data = {
        "$schema": "https://mef.rero.ch/schemas/concepts_idref/idref-concept-v0.0.1.json",
        "authorized_access_point": "Agriculture biologique",
        "identifiedBy": [
            {"source": "IDREF", "type": "uri", "value": "http://www.idref.fr/027229080"},
            {"source": "BNF", "type": "bf:Nbn", "value": "FRBNF11930852"},
        ],
        "pid": "027229080",
        "type": "bf:Topic",
    }
    rero_record, _ = ConceptReroRecord.create_or_update(
        data=deepcopy(concept_rero_link_data), dbcommit=True, reindex=True
    )
    gnd_record, _ = ConceptGndRecord.create_or_update(
        data=deepcopy(concept_gnd_rero_link_data), dbcommit=True, reindex=True
    )
    idref_record, _ = ConceptIdrefRecord.create_or_update(data=idref_data, dbcommit=True, reindex=True)
    ConceptReroRecord.flush_indexes()
    ConceptGndRecord.flush_indexes()
    ConceptIdrefRecord.flush_indexes()

    rero_record.create_or_update_mef(dbcommit=True, reindex=True)
    mef_record, _ = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    ConceptMefRecord.flush_indexes()

    assert _refs(mef_record) == {"idref", "gnd"}
    rero_mef_records = ConceptMefRecord.get_mef(entity_name="rero", entity_pid=rero_record.pid)
    assert len(rero_mef_records) == 1
    assert _refs(rero_mef_records[0]) == {"rero"}
    assert rero_mef_records[0].pid != mef_record.pid
    assert gnd_record.association.identifiers == idref_record.association.identifiers
