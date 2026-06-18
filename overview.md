<!--
SPDX-FileCopyrightText: Fondation RERO+
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# RERO MEF Data Model Overview

View and edit diagrams at: [mermaid.live](https://mermaid.live)

## Agent Records

```mermaid
classDiagram
    direction TB

    class AgentMefRecord {
        <<MEF Aggregator>>
        +String pid
        +Reference idref
        +Reference gnd
        +Reference rero
        +String viaf_pid
        +String type
    }

    class AgentViafRecord {
        <<VIAF Aggregator>>
        +String pid
        +String idref_pid
        +String gnd_pid
        +String rero_pid
    }

    class AgentIdrefRecord {
        <<IdRef Source>>
        +String pid
        +Object[] identifiedBy
        +String[] authorized_access_point
        +String md5
        +String[] language
        +String gender
        +String date_of_birth
        +String date_of_death
        +String[] biographical_information
        +String preferred_name
        +String qualifier
        +String numeration
        +String[] variant_name
        +String date_of_establishment
        +String date_of_termination
        +Boolean conference
        +String[] variant_access_point
        +String[] parallel_access_point
        +String country_associated
        +String deleted
        +Object relation_pid
    }

    class AgentGndRecord {
        <<GND Source>>
        +String pid
        +Object[] identifiedBy
        +String[] authorized_access_point
        +String md5
        +String[] language
        +String gender
        +String date_of_birth
        +String date_of_death
        +String[] biographical_information
        +String preferred_name
        +String qualifier
        +String numeration
        +String[] variant_name
        +String date_of_establishment
        +String date_of_termination
        +Boolean conference
        +String[] variant_access_point
        +String[] parallel_access_point
        +String country_associated
        +String deleted
        +Object relation_pid
    }

    class AgentReroRecord {
        <<RERO Source>>
        +String pid
        +Object[] identifiedBy
        +String[] authorized_access_point
        +String md5
        +String[] language
        +String gender
        +String date_of_birth
        +String date_of_death
        +String[] biographical_information
        +String preferred_name
        +String qualifier
        +String numeration
        +String[] variant_name
        +String date_of_establishment
        +String date_of_termination
        +Boolean conference
        +String[] variant_access_point
        +String[] parallel_access_point
        +String country_associated
        +String deleted
        +Object relation_pid
    }

    AgentIdrefRecord --> AgentMefRecord : aggregated via VIAF
    AgentGndRecord --> AgentMefRecord : aggregated via VIAF
    AgentReroRecord --> AgentMefRecord : aggregated via VIAF
    AgentViafRecord ..> AgentMefRecord : provides linking
    AgentViafRecord --> AgentIdrefRecord : links via idref_pid
    AgentViafRecord --> AgentGndRecord : links via gnd_pid
    AgentViafRecord --> AgentReroRecord : links via rero_pid
```

## Concept Records

> **No VIAF integration:** VIAF (Virtual International Authority File) only aggregates
> name authority records — persons, corporate bodies, and families. It does not cover
> subject/concept authority records, so there is no `ConceptViafRecord` equivalent and
> `ConceptMefRecord` carries no `viaf_pid` field.
>
> **Linking mechanism:** Concept records are linked directly via cross-reference
> identifiers embedded in each source record's `identifiedBy` field (e.g. a BNF code
> such as `FRBNF12345678` stored by an IdRef record, or a GND code stored by a GND
> record). The `association_identifier` property extracts this identifier and
> `get_association_record()` uses it to locate the counterpart record in another source.
> Both are then stored as `$ref` links inside a shared `ConceptMefRecord`.

```mermaid
classDiagram
    direction TB

    class ConceptMefRecord {
        <<MEF Aggregator>>
        +String pid
        +Reference idref
        +Reference gnd
        +Reference rero
        +String type
    }

    class ConceptIdrefRecord {
        <<IdRef Source>>
        +String pid
        +String md5
        +Object[] identifiedBy
        +String bnf_type
        +String[] authorized_access_point
        +String[] variant_access_point
        +Object[] broader
        +Object[] related
        +Object[] narrower
        +Object[] classification
        +String[] note
        +String[] closeMatch
        +String deleted
        +Object relation_pid
    }

    class ConceptGndRecord {
        <<GND Source>>
        +String pid
        +String md5
        +Object[] identifiedBy
        +String[] authorized_access_point
        +String[] variant_access_point
        +Object[] broader
        +Object[] related
        +Object[] narrower
        +Object[] classification
        +String[] note
        +String[] closeMatch
        +String deleted
        +Object relation_pid
    }

    class ConceptReroRecord {
        <<RERO Source>>
        +String pid
        +String md5
        +Object[] identifiedBy
        +String bnf_type
        +String[] authorized_access_point
        +String[] variant_access_point
        +Object[] broader
        +Object[] related
        +Object[] narrower
        +Object[] classification
        +String[] note
        +String[] closeMatch
        +String deleted
        +Object relation_pid
    }

    ConceptIdrefRecord --> ConceptMefRecord : linked via association identifier
    ConceptGndRecord --> ConceptMefRecord : linked via association identifier
    ConceptReroRecord --> ConceptMefRecord : linked via association identifier
```

## Place Records

> **Note:** RERO does not publish place authority data, so there is no PlaceReroRecord
> and `PlaceMefRecord` has no `rero` reference field. This is intentional and differs
> from the Agent and Concept sections where all three sources (IdRef, GND, RERO) exist.
>
> **Linking mechanism:** Same association-identifier pattern as Concept records. An
> IdRef place record carries a GND code in its `identifiedBy` field (source `"GND"`,
> value prefixed with `"(DE-101)"`). The `association_identifier` property strips the
> prefix and uses it to locate the matching `PlaceGndRecord`, which is then stored
> together with the IdRef record as `$ref` links inside a shared `PlaceMefRecord`.

```mermaid
classDiagram
    direction TB

    class PlaceMefRecord {
        <<MEF Aggregator>>
        +String pid
        +Reference idref
        +Reference gnd
        +String type
    }

    class PlaceIdrefRecord {
        <<IdRef Source>>
        +String pid
        +String md5
        +Object[] identifiedBy
        +String bnf_type
        +String[] authorized_access_point
        +String[] variant_access_point
        +Object[] broader
        +Object[] related
        +Object[] narrower
        +String[] note
        +String[] closeMatch
        +String deleted
        +Object relation_pid
    }

    class PlaceGndRecord {
        <<GND Source>>
        +String pid
        +String md5
        +Object[] identifiedBy
        +String[] authorized_access_point
        +String[] variant_access_point
        +Object[] broader
        +Object[] related
        +Object[] narrower
        +String[] note
        +String[] closeMatch
        +String deleted
        +Object relation_pid
    }

    PlaceIdrefRecord --> PlaceMefRecord : linked via association identifier
    PlaceGndRecord --> PlaceMefRecord : linked via association identifier
```
