# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test that the external authority services stay out of reach.

Only the refusals are asserted, so these never open a connection themselves.
"""

import pytest
import requests

from tests.blocked_sources import BLOCKED_HOSTS

GND = "https://services.dnb.de/oai/repository?verb=Identify"
IDREF = "https://www.idref.fr/026361477.rdf"
VIAF = "https://viaf.org/viaf/64591951/justlinks.json"


@pytest.mark.parametrize(("url", "source"), [(GND, "gnd"), (IDREF, "idref"), (VIAF, "viaf")])
def test_the_authority_services_are_out_of_reach(url, source):
    """A test that asks for nothing reaches none of them."""
    with pytest.raises(requests.exceptions.ConnectionError) as err:
        requests.get(url, timeout=5)
    assert source in str(err.value)
    assert "did not ask for" in str(err.value)


@pytest.mark.online("gnd")
def test_the_marker_opens_one_source_only():
    """Asking for GND says nothing about IdRef."""
    with pytest.raises(requests.exceptions.ConnectionError) as err:
        requests.get(IDREF, timeout=5)
    assert "idref" in str(err.value)


def test_every_blocked_host_names_a_source():
    """The marker takes a source name, so each host has to map to one."""
    assert set(BLOCKED_HOSTS.values()) == {"idref", "gnd", "viaf"}
