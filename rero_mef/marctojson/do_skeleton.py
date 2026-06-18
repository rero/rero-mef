# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

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
class Transformation:
    """Transformation skeleton for MARC to json."""

    def __init__(self, marc, logger=None, verbose=False, transform=True):
        """Constructor."""
        self.marc = marc
        self.logger = logger
        self.verbose = verbose
        self.json_dict = {}
        if transform:
            self._transform()

    def _transform(self):
        """Call the transformation functions."""
        for func in dir(self):
            if func.startswith("trans"):
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
            self.logger.info("Transformation: %s", "trans_example_1")
        fields_001 = self.marc.get_fields("001")
        # save the conferted data to json_dict
        self.json_dict["example1"] = fields_001[0].data

    def trans_example_2(self):
        """Transformation example 2."""
        if self.logger and self.verbose:
            self.logger.info("Call Function: %s", "trans_example_2")
        fields_245 = self.marc.get_fields("245")
        to_return = []
        for field in fields_245:
            data = {}
            if value := field.get("a"):
                data["ex2_a"] = value
            if value := field.get("b"):
                data["ex2_b"] = value
            if value := field.get("c"):
                data["ex2_c"] = value
            to_return.append(data)
        # save the conferted data to json_dict
        self.json_dict["example2"] = to_return
