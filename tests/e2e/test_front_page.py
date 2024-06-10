"""E2E test of the front page."""

from flask import url_for


def test_frontpage(live_server, browser):
    """Test retrieval of front page."""
    browser.get(url_for("rero_mef.index", _external=True))
    # print(browser.page_source)
    # TODO: write tests
