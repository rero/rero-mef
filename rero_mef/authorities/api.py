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

"""API for manipulating authorities."""

from invenio_search.api import RecordsSearch

from ..api import AuthRecord
from .fetchers import bnf_id_fetcher, gnd_id_fetcher, mef_id_fetcher, \
    rero_id_fetcher, viaf_id_fetcher
from .minters import bnf_id_minter, gnd_id_minter, mef_id_minter, \
    rero_id_minter, viaf_id_minter
from .providers import BnfProvider, GndProvider, MefProvider, ReroProvider, \
    ViafProvider


class ViafSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'authorities-viaf-person-v0.0.1'


class BnfSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'authorities-bnf-person-v0.0.1'


class ReroSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'authorities-rero-person-v0.0.1'


class GndSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'authorities-gnd-person-v0.0.1'


class MefSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'authorities-mef-person-v0.0.1'


class MefRecord(AuthRecord):
    """Mef Authority class."""

    minter = mef_id_minter
    fetcher = mef_id_fetcher
    provider = MefProvider


class GndRecord(AuthRecord):
    """Gnd Authority class."""

    minter = gnd_id_minter
    fetcher = gnd_id_fetcher
    provider = GndProvider


class ReroRecord(AuthRecord):
    """Rero Authority class."""

    minter = rero_id_minter
    fetcher = rero_id_fetcher
    provider = ReroProvider


class BnfRecord(AuthRecord):
    """Bnf Authority class."""

    minter = bnf_id_minter
    fetcher = bnf_id_fetcher
    provider = BnfProvider


class ViafRecord(AuthRecord):
    """Viaf Authority class."""

    minter = viaf_id_minter
    fetcher = viaf_id_fetcher
    provider = ViafProvider
