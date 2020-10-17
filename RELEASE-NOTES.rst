..
    This file is part of RERO MEF.
    Copyright (C) 2018 RERO.

    RERO MEF is free software; you can redistribute it
    and/or modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    RERO MEF is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with RERO MEF; if not, write to the
    Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
    MA 02111-1307, USA.

    In applying this license, RERO does not
    waive the privileges and immunities granted to it by virtue of its status
    as an Intergovernmental Organization or submit itself to any jurisdiction.

v0.3.0
======

-  Fixes wrong VIAF PIDs in MEF records.
-  Updates VIAF, RERO, GND data.
-  Adds tests to spot duplicated PIDs.
-  Updates metadata model transformation (from MARC to JSON).
-  Updates Invenio to version ``3.2.1``.
-  Integrates IdRef:

   -  Harvest IdRef through OAI-PMH.
   -  Adds IdRef to MEF records.

-  Harvest GND through OAI-PMH instead of importing dumps.
-  Uses separate postgresql tables for each source.
-  Issues:

   -  `rero/rero-ils#555 <https://github.com/rero/rero-ils/issues/555>`__:
      Jean-Paul II was missing!
   -  `rero/rero-ils#657 <https://github.com/rero/rero-ils/issues/657>`__:
      Add the qualifier of a person in the title of the brief and
      detailed view (in RERO ILS).

v0.2.0
======

-  Data:

   -  Updates agents (source) data.
   -  Improves transformation to ``preferred_name`` to keep
      regnal numbers.

-  Search:

   -  Removes ES v2 mappings.
   -  Adds source field to ES mappings.
   -  Uses AND as the default ES query boolean operator.

-  Ignores versioning of ``.env`` and celerybeat directory.
-  Extends CLI with an utility to create ``csv`` agent files.
-  Improves bulk loading of big files with chunks.
-  Adds a serializer to resolve JSON references.
-  Moves deployment files to an external git repository.
-  Fixes links in the README file.
-  Issues:

   -  `#11 <https://github.com/rero/rero-mef/issues/11>`__: Avoids
      loading non person authority record from the BNF.
   -  `#32 <https://github.com/rero/rero-mef/issues/32>`__: Removes
      unnecessary prefix for sources PIDs and duplicate PIDs.
   -  `#33 <https://github.com/rero/rero-mef/issues/33>`__: Fixes
      variant name for a person transformation, to get complete variant
      name.
