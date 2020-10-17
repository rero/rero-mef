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

"""JSON schemas utils."""

from invenio_jsonschemas.proxies import current_jsonschemas
from jsonref import JsonLoader as JsonRefLoader

try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache


class JsonLoader(JsonRefLoader):
    """Json schema loader.

    We have to add local $ref loading to the base class.
    https://invenio-jsonschemas.readthedocs.io/en/latest/configuration.html
    """

    @lru_cache(maxsize=1000)
    def get_remote_json(self, uri, **kwargs):
        """Get remote json.

        Adds loading of $ref locally for the application instance.
        See: github invenio-jsonschemas ext.py.
        :param uri: The URI of the JSON document to load.
        :param kwargs: Keyword arguments passed to json.loads().
        :returns: resolved json schema.
        """
        path = current_jsonschemas.url_to_path(uri)
        if path:
            result = current_jsonschemas.get_schema(path=path)
        else:
            result = super().get_remote_json(uri, **kwargs)
        return result
