# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Keep the tests off the external authority services.

Nothing in the suite needs IdRef, GND or VIAF: the tests that exercise an online lookup mock the HTTP call. Letting
a real one through would make a test depend on a service being up and on what it serves today, so the hosts are
refused by default and a test that really wants one has to say so:

    @pytest.mark.online("gnd")
    def test_something(...):

`--allow-online` lifts the block for a whole run, for when you do want to check the live services.
"""

import pytest
import urllib3.util.connection as urllib3_connection

#: Host -> the source it belongs to, as named by `@pytest.mark.online`.
BLOCKED_HOSTS = {
    "www.idref.fr": "idref",
    "idref.fr": "idref",
    "services.dnb.de": "gnd",
    "d-nb.info": "gnd",
    "viaf.org": "viaf",
    "www.viaf.org": "viaf",
}

_real_create_connection = urllib3_connection.create_connection


class BlockedSourceError(OSError):
    """A test reached an external authority service it did not ask for."""


def pytest_addoption(parser):
    """Add the option that lifts the block."""
    parser.addoption("--allow-online", action="store_true", default=False, help="Let the tests reach IdRef/GND/VIAF.")


def pytest_configure(config):
    """Register the marker."""
    config.addinivalue_line("markers", "online(*sources): let this test reach idref, gnd or viaf")


@pytest.fixture(autouse=True)
def block_external_sources(request):
    """Refuse connections to the authority services this test did not ask for.

    :param request: Pytest request, read for the `online` marker.
    """
    if request.config.getoption("--allow-online"):
        yield
        return
    allowed = {source for marker in request.node.iter_markers("online") for source in marker.args}

    def guard(address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else address
        source = BLOCKED_HOSTS.get(str(host))
        if source is not None and source not in allowed:
            raise BlockedSourceError(
                f"{host} belongs to {source}, which this test did not ask for. Mock the call, or mark the test "
                f'`@pytest.mark.online("{source}")`, or run with --allow-online.'
            )
        return _real_create_connection(address, *args, **kwargs)

    urllib3_connection.create_connection = guard
    try:
        yield
    finally:
        urllib3_connection.create_connection = _real_create_connection
