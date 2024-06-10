# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2020 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""JS/CSS bundles for rero-mef.

You include one of the bundles in a page like the example below (using
``base`` bundle as an example):
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
