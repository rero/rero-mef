# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Single source of truth for the shared French/German search-analysis setup.

Applies across the MEF and standalone-source Elasticsearch mapping files.
Elasticsearch's mapping API takes a literal, self-contained JSON document --
it has no ``$ref``, and invenio-search's loader does a bare ``json.load()``
of each file, so the same filter/analyzer chain has to be physically
duplicated across all 11 mapping files that carry ``authorized_access_point``
/``variant_access_point`` (plus, for agents, ``variant_name`` and
``parallel_access_point``): the 3 MEF aggregation mappings (``agents/mef``,
``concepts/mef``, ``places/mef``) and the 8 standalone per-source mappings
(``agents|concepts|places`` x ``gnd|idref|rero``, minus ``places/rero``
which doesn't exist).

Hand-copying that chain into 11 files is exactly what caused the drift this
module fixes: ``ascii_folding`` was missing from all 8 standalone files
while present in the 3 MEF ones. Defining the chain once here, and either
writing it out (``write``) or checking the files already match
(``check_all``, used by tests/unit/test_mapping_analysis.py), makes that
drift impossible instead of just less likely.

Deliberately NOT decompounded: agent personal/organisation names. German
dictionary_decompounder splits surnames that happen to look like compounds
(e.g. "Bergmann" -> "berg" + "mann", verified live against the real
dictionary), so ``agents/gnd`` gets ``german_normalization`` only, never
``german_decompounder``. Concepts and places (subject headings, place and
institution names) get the full decompounder.
"""

import json
from copy import deepcopy
from pathlib import Path

import click

REPO_ROOT = Path(__file__).resolve().parent.parent

FRENCH_ELISION_FILTER = {
    "type": "elision",
    "articles_case": True,
    "articles": [
        "l",
        "m",
        "t",
        "qu",
        "n",
        "s",
        "j",
        "d",
        "c",
        "jusqu",
        "quoiqu",
        "lorsqu",
        "puisqu",
    ],
}

GERMAN_DECOMPOUNDER_FILTER = {
    "type": "hyphenation_decompounder",
    "word_list_path": "analysis/dictionary-de.txt",
    "hyphenation_patterns_path": "analysis/de_DR.xml",
    "only_longest_match": True,
    "min_subword_size": 4,
}

AUTOCOMPLETE_FILTER = {
    "type": "edge_ngram",
    "min_gram": 1,
    "max_gram": 20,
}

ASCII_FOLDING_FILTER = {
    "type": "asciifolding",
    "preserve_original": True,
}

#: Fields to give a language-aware analyzer. Agents get two extra naming
#: fields (concepts/places don't have them); preferred_name is deliberately
#: excluded everywhere -- it's already folded into authorized_access_point.
STANDARD_FIELDS = ["authorized_access_point", "variant_access_point"]
AGENT_FIELDS = [*STANDARD_FIELDS, "variant_name", "parallel_access_point"]


def french_access_point_analyzer():
    """Analyzer for French (idref/rero) naming fields."""
    return {
        "type": "custom",
        "tokenizer": "standard",
        "filter": ["french_elision", "lowercase", "my_ascii_folding"],
    }


def german_access_point_analyzer(decompound):
    """Analyzer for German (gnd) naming fields.

    :param decompound: include the hyphenation_decompounder step. Must stay
        False for agents (surname-fragmentation risk).
    """
    filters = ["lowercase", "german_normalization"]
    if decompound:
        filters.append("german_decompounder")
    filters.append("my_ascii_folding")
    return {"type": "custom", "tokenizer": "standard", "filter": filters}


def autocomplete_analyzer(decompound):
    """Index-time analyzer for the MEF-level aggregated autocomplete_name field."""
    filters = ["french_elision", "lowercase", "german_normalization"]
    if decompound:
        filters.append("german_decompounder")
    filters += ["autocomplete_filter", "my_ascii_folding"]
    return {"type": "custom", "tokenizer": "standard", "filter": filters}


def autocomplete_search_analyzer(decompound):
    """Search-time analyzer matching :func:`autocomplete_analyzer` minus the ngram step."""
    filters = ["french_elision", "lowercase", "german_normalization"]
    if decompound:
        filters.append("german_decompounder")
    filters.append("my_ascii_folding")
    return {"type": "custom", "tokenizer": "standard", "filter": filters}


def _languages_used(spec):
    if spec["kind"] == "mef":
        return set(spec["sources"].values())
    return {spec["language"]}


def build_analysis_settings(spec):
    """Build the full ``settings.analysis`` block for a mapping spec.

    :param spec: one entry of :data:`MAPPING_SPECS`.
    :returns: dict suitable for ``mapping["settings"]["analysis"]``.
    """
    filters = {}
    analyzers = {}
    languages = _languages_used(spec)
    decompound = spec.get("decompound", False)

    if "french" in languages:
        filters["french_elision"] = FRENCH_ELISION_FILTER
        analyzers["french_access_point"] = french_access_point_analyzer()
    if "german" in languages:
        if decompound:
            filters["german_decompounder"] = GERMAN_DECOMPOUNDER_FILTER
        analyzers["german_access_point"] = german_access_point_analyzer(decompound)

    filters["my_ascii_folding"] = ASCII_FOLDING_FILTER
    if spec["kind"] == "mef":
        filters["autocomplete_filter"] = AUTOCOMPLETE_FILTER
        analyzers["autocomplete"] = autocomplete_analyzer(decompound)
        analyzers["autocomplete_search"] = autocomplete_search_analyzer(decompound)

    return {"filter": filters, "analyzer": analyzers}


def _analyzer_name_for(language):
    return "german_access_point" if language == "german" else "french_access_point"


def _set_field_analyzer(props, field, analyzer_name, add_raw):
    if field not in props:
        return
    props[field]["analyzer"] = analyzer_name
    if add_raw:
        # Keep any other sub-field the mapping declares, only `raw` is ours.
        props[field].setdefault("fields", {})["raw"] = {"type": "keyword"}


def apply_spec(mapping, spec):
    """Return a copy of `mapping` with the shared analysis settings applied.

    Idempotent: applying the same spec twice produces the same result, so
    this can run directly against an already-patched file on disk.

    :param mapping: parsed mapping JSON (dict).
    :param spec: one entry of :data:`MAPPING_SPECS`.
    :returns: new dict, `mapping` is not mutated.
    """
    mapping = deepcopy(mapping)
    mapping.setdefault("settings", {})["analysis"] = build_analysis_settings(spec)
    add_raw = spec.get("add_raw", False)

    if spec["kind"] == "mef":
        for source, language in spec["sources"].items():
            analyzer_name = _analyzer_name_for(language)
            source_props = mapping["mappings"]["properties"][source]["properties"]
            for field in spec["fields"]:
                _set_field_analyzer(source_props, field, analyzer_name, add_raw)
        autocomplete = mapping["mappings"]["properties"]["autocomplete_name"]
        autocomplete["analyzer"] = "autocomplete"
        autocomplete["search_analyzer"] = "autocomplete_search"
    else:
        analyzer_name = _analyzer_name_for(spec["language"])
        props = mapping["mappings"]["properties"]
        for field in spec["fields"]:
            _set_field_analyzer(props, field, analyzer_name, add_raw)

    return mapping


MAPPING_SPECS = [
    {
        "path": "rero_mef/agents/mef/mappings/v7/mef/mef-v0.0.1.json",
        "kind": "mef",
        "sources": {"gnd": "german", "idref": "french", "rero": "french"},
        "decompound": False,
        "fields": AGENT_FIELDS,
        "add_raw": True,
    },
    {
        "path": "rero_mef/concepts/mef/mappings/v7/concepts_mef/mef-concept-v0.0.1.json",
        "kind": "mef",
        "sources": {"gnd": "german", "idref": "french", "rero": "french"},
        "decompound": True,
        "fields": STANDARD_FIELDS,
        "add_raw": True,
    },
    {
        "path": "rero_mef/places/mef/mappings/v7/places_mef/mef-place-v0.0.1.json",
        "kind": "mef",
        "sources": {"gnd": "german", "idref": "french"},
        "decompound": True,
        "fields": STANDARD_FIELDS,
        "add_raw": True,
    },
    {
        "path": "rero_mef/agents/gnd/mappings/v7/agents_gnd/gnd-agent-v0.0.1.json",
        "kind": "standalone",
        "language": "german",
        "decompound": False,
        "fields": AGENT_FIELDS,
        "add_raw": True,
    },
    {
        "path": "rero_mef/agents/idref/mappings/v7/agents_idref/idref-agent-v0.0.1.json",
        "kind": "standalone",
        "language": "french",
        "fields": AGENT_FIELDS,
        "add_raw": True,
    },
    {
        "path": "rero_mef/agents/rero/mappings/v7/agents_rero/rero-agent-v0.0.1.json",
        "kind": "standalone",
        "language": "french",
        "fields": AGENT_FIELDS,
        "add_raw": True,
    },
    {
        "path": "rero_mef/concepts/gnd/mappings/v7/concepts_gnd/gnd-concept-v0.0.1.json",
        "kind": "standalone",
        "language": "german",
        "decompound": True,
        "fields": STANDARD_FIELDS,
        "add_raw": True,
    },
    {
        "path": "rero_mef/concepts/idref/mappings/v7/concepts_idref/idref-concept-v0.0.1.json",
        "kind": "standalone",
        "language": "french",
        "fields": STANDARD_FIELDS,
        "add_raw": True,
    },
    {
        "path": "rero_mef/concepts/rero/mappings/v7/concepts_rero/rero-concept-v0.0.1.json",
        "kind": "standalone",
        "language": "french",
        "fields": STANDARD_FIELDS,
        "add_raw": True,
    },
    {
        "path": "rero_mef/places/gnd/mappings/v7/places_gnd/gnd-place-v0.0.1.json",
        "kind": "standalone",
        "language": "german",
        "decompound": True,
        "fields": STANDARD_FIELDS,
        "add_raw": True,
    },
    {
        "path": "rero_mef/places/idref/mappings/v7/places_idref/idref-place-v0.0.1.json",
        "kind": "standalone",
        "language": "french",
        "fields": STANDARD_FIELDS,
        "add_raw": True,
    },
]


def check_all(verbose=False):
    """Compare every mapping file on disk against what its spec would generate.

    :param verbose: echo each file path as it's checked.
    :returns: list of (path, disk_json, expected_json) tuples for files that
        differ. Empty list means everything is in sync.
    """
    mismatches = []
    for spec in MAPPING_SPECS:
        if verbose:
            click.echo(f"checking {spec['path']}")
        file_path = REPO_ROOT / spec["path"]
        on_disk = json.loads(file_path.read_text())
        expected = apply_spec(on_disk, spec)
        if on_disk != expected:
            mismatches.append((spec["path"], on_disk, expected))
    return mismatches


def write_all(verbose=False):
    """Regenerate the analysis settings of every mapping file from its spec.

    :param verbose: echo each file path as it's written.
    """
    for spec in MAPPING_SPECS:
        if verbose:
            click.echo(f"writing {spec['path']}")
        file_path = REPO_ROOT / spec["path"]
        on_disk = json.loads(file_path.read_text())
        updated = apply_spec(on_disk, spec)
        file_path.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n")


@click.group()
def mapping_analysis():
    """Manage the shared French/German search-analysis mapping settings.

    Runs standalone -- no Flask app context, database, or Elasticsearch
    connection needed, since it only reads/writes the mapping JSON files.
    """


@mapping_analysis.command("check")
@click.option("-v", "--verbose", is_flag=True, help="Echo each file path as it's checked.")
def check_command(verbose):
    """Exit non-zero if any mapping file has drifted from its spec."""
    if problems := check_all(verbose=verbose):
        for path, _, _ in problems:
            click.echo(f"OUT OF SYNC: {path}")
        raise SystemExit(1)
    click.echo(f"All {len(MAPPING_SPECS)} mapping files match their spec.")


@mapping_analysis.command("write")
@click.option("-v", "--verbose", is_flag=True, help="Echo each file path as it's written.")
def write_command(verbose):
    """Regenerate every mapping file's analysis settings from the shared spec."""
    write_all(verbose=verbose)
    click.echo(f"Regenerated {len(MAPPING_SPECS)} mapping files.")


if __name__ == "__main__":
    mapping_analysis()
