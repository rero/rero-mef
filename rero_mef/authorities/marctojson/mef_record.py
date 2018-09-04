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

"""Marctojsons transformer skeleton."""


# ---------------------------- Modules ----------------------------------------
# import of standard modules
import hashlib
import json

# third party modules

# local modules

__author__ = "Gianni Pante <Gianni Pante@rero.ch>"
__version__ = "0.0.1"
__copyright__ = "Copyright (c) 2009-2018 Rero, Gianni Pante"
__license__ = "Internal Use Only"


# ----------------------------------- Classes ---------------------------------

# MrcIterator ----
class MEF_record(object):
    """Transformation unimarc to json/bnf auth person."""

    def __init__(self, json_data, logger=None, verbose=False):
        """Constructor."""
        self.json_dict = json_data
        self.logger = logger
        self.verbose = verbose

    def _add_source(self, source, json_data):
        """Add the given authority data."""
        for field_key in json_data:
            if field_key not in self.json_dict:
                self.json_dict[field_key] = []
            source_data = {}
            source_data['source'] = source
            source_data['value'] = json_data[field_key]
            self.json_dict[field_key].append(source_data)

    @property
    def json(self):
        """Json data."""
        return self.json_dict

    @classmethod
    def add_md5_to_json(cls, json_data):
        """Add md5 to json."""
        data_md5 = hashlib.md5(
            json.dumps(json_data, sort_keys=True).encode('utf-8')).hexdigest()
        json_data['md5'] = data_md5

    def get_source_md5(self, source):
        """Get the JSON MD5 of the given source."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", 'get_source_md5')
        md5 = None
        if 'md5' in self.json_dict:
            for index, data in enumerate(self.json_dict['md5'], start=0):
                if data['source'] == source:
                    md5 = data['value']
                    break
        return md5

    def delete_source(self, source):
        """Delete the given authority data."""
        "Remove the given authority data."""
        for field_key in self.json_dict:
            for index, data in enumerate(self.json_dict[field_key], start=0):
                if data['source'] == source:
                    print("del source", source)
                    del self.json_dict[field_key][index]
                    break

    def update_source(self, source, json_data, force=False):
        """update_source JSON data."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", 'update_source')
        md5_source = self.get_source_md5(source)
        if 'md5' not in json_data:
            self.add_md5_to_json(json_data)
        if force or json_data['md5'] != md5_source:
            self.delete_source(source)
            self._add_source(source, json_data)
