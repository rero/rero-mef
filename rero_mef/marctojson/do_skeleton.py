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

"""Marctojsons transformer skeleton."""

# ---------------------------- Modules ----------------------------------------
# import of standard modules

# third party modules

# local modules

__author__ = "Johnny Mariethoz <Johnny.Mariethoz@rero.ch>"
__version__ = "0.0.1"
__copyright__ = "Copyright (c) 2009-2011 Rero, Johnny Mariethoz"
__license__ = "Internal Use Only"


# ----------------------------------- Classes ---------------------------------
# MrcIterator ----
class Transformation(object):
    """Transformation skeleton for MARC to json."""

    def __init__(self, marc, logger=None, verbose=False, transform=True):
        """Constructor."""
        self.marc = marc
        self.logger = logger
        self.verbose = verbose
        self.json_dict = {}
        self.needs_tags = []
        if transform:
            self._transform()

    def _transform(self):
        """Call the transformation functions."""
        for func in dir(self):
            if func.startswith('trans'):
                func = getattr(self, func)
                func()

    @property
    def json(self):
        """Json data."""
        return self.json_dict

    # transformation functions have to start with trans:
    def trans_example_1(self):
        """Transformation example 1."""
        if self.logger and self.verbose:
            self.logger.info("Transformation", 'trans_example_1')
        fields_001 = self.marc.get_fields('001')
        # save the conferted data to json_dict
        self.json_dict['example1'] = fields_001[0].data

    def trans_example_2(self):
        """Transformation example 2."""
        if self.logger and self.verbose:
            self.logger.info("Call Function", 'trans_example_1')
        fields_245 = self.marc.get_fields('245')
        to_return = []
        for field in fields_245:
            data = {}
            if field.get_subfields('a'):
                data['ex2_a'] = field.get_subfields('a')[0]
            if field.get_subfields('b'):
                data['ex2_b'] = field.get_subfields('b')[0]
            if field.get_subfields('c'):
                data['ex2_c'] = field.get_subfields('c')[0]
            to_return.append(data)
        # save the conferted data to json_dict
        self.json_dict['example2'] = to_return
