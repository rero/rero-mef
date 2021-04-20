---
title: Release notes
copyright: Copyright (C) 2020 RERO
license: GNU Affero General Public License
---

## v0.7.0

## Data

- Fixes `bf:Organisation` records with `conference=true`.

### CLI

- Improves `csv_diff` performance by using `pickeldb` to reduce memory usage
  during `csv_diff` operation.

### API

- Improves DB error handling for `get_record_by_pid`.
- Improves persistent identifier handling.
- Corrects error management (raise of exceptions).

### Monitoring

- Monitors REDIS, timestamp and ElasticSearch.

### Instance

- Moves the license from the GPLv2 to the AGPLv3.
- Upgrades Invenio to `v3.4`.
- Upgrades dependencies.

## v0.6.0

### Metadata management

- Implements `AgentClass` for all agents.
- Improves handling of agent *creation* and *update*.
- Renames MARC transformation files.
- Implements concepts for RERO Rameau.
- Adds `autocomplete_name` to MEF mappings.

### Search

- Uses [ICU analysis][2] plugin for ElasticSearch.

### Authority file import

- Adds numbering and qualifier to transformation.
- Allows to enqueue the *create* and *update* task.
- Adds *creation*, *update*, *deletion* of VIAF records.
- Allows to get records from BnF through the SRU service.
- Removes the BnF source (replaced by IdRef in `v0.3.0`)
- Adds corporate body to the contribution records.
- Tags record as deleted when the source is deleted.
- Saves OAI harvesting to file.

### Instance

- Uses `poetry` for python dependencies management.
- Upgrades `invenio` to version `3.3`.
- Upgrades ElasticSearch to version `7`.
- Moves to GitHub actions for *Continuous integration* (CI).
- Rewrites codes to simplify.
- Monitors the API.
- Moves assets management to webpack.

## v0.3.0

- Fixes wrong VIAF PIDs in MEF records.
- Updates VIAF, RERO, GND data.
- Adds tests to spot duplicated PIDs.
- Updates metadata model transformation (from MARC to JSON).
- Updates Invenio to version `3.2.1`.
- Integrates IdRef:
  - Harvest IdRef through OAI-PMH.
  - Adds IdRef to MEF records.
- Harvest GND through OAI-PMH instead of importing dumps.
- Uses separate postgresql tables for each source.
- Issues:
  - [rero/rero-ils\#555][i555]: Jean-Paul II was missing!
  - [rero/rero-ils#657][i657]: Add the qualifier of a person in the title of
    the brief and detailed view (in RERO ILS).

## v0.2.0

- Data:
  - Updates agents (source) data.
  - Improves transformation to `preferred_name` to keep regnal numbers.
- Search:
  - Removes ES v2 mappings.
  - Adds source field to ES mappings.
  - Uses AND as the default ES query boolean operator.
- Ignores versioning of `.env` and celerybeat directory.
- Extends CLI with an utility to create `csv` agent files.
- Improves bulk loading of big files with chunks.
- Adds a serializer to resolve JSON references.
- Moves deployment files to an external git repository.
- Fixes links in the [README.rst][1] file.
- Issues:
  - [#11][i11]: Avoids loading non person authority record from the BNF.
  - [#32][i32]: Removes unnecessary prefix for sources PIDs and duplicate
    PIDs.
  - [#33][i33]: Fixes variant name for a person transformation, to get
    complete variant name.

[1]: README.rst
[2]: https://www.elastic.co/guide/en/elasticsearch/plugins/current/analysis-icu.html
[i11]: https://github.com/rero/rero-mef/issues/11
[i32]: https://github.com/rero/rero-mef/issues/32
[i33]: https://github.com/rero/rero-mef/issues/33
[i555]: https://github.com/rero/rero-ils/issues/555
[i657]: https://github.com/rero/rero-ils/issues/657
