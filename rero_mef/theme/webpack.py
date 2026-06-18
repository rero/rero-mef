# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""JS/CSS bundles for rero-mef.

You include one of the bundles in a page like the example below (using ``base`` bundle as an example):
.. code-block:: html

   {{ webpack['base.js']}}
"""

from flask_webpackext import WebpackBundle, WebpackBundleProject
from pywebpack import bundles_from_entry_point

project = WebpackBundleProject(
    __name__,
    project_folder="webpack_assets",
    config_path="build/config.json",
    bundles=bundles_from_entry_point("invenio_assets.webpack"),
)

theme = WebpackBundle(
    __name__,
    "assets",
    entry={"global": "./scss/rero_mef/mef.scss"},
)
