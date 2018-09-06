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

"""Marctojsons module to hanle the Marc records."""

# ---------------------------- Modules ----------------------------------------
# import of standard modules
import pymarc

# third party modules

# local modules

__author__ = "Johnny Mariethoz <Johnny.Mariethoz@rero.ch>"
__version__ = "0.0.1"
__copyright__ = "Copyright (c) 2009-2011 Rero, Johnny Mariethoz"
__license__ = "Internal Use Only"


# ----------------------------------- Classes ---------------------------------
# MrcIterator ----
class MrcIterator(object):
    """Iterator to get marc records from mrc file."""

    def __init__(self, file_name, exceptions=False):
        """DocString."""
        self.error = None
        self._marc_reader = pymarc.MARCReader(open(file_name, 'rb'),
                                              to_unicode=True,
                                              force_utf8=True,
                                              utf8_handling='ignore')
        self.error = ''
        self.exceptions = exceptions

    def __next_valid__(self, error):
        """Get next valid marc record."""
        try:
            rec = self._marc_reader.__next__()
        except StopIteration:
            return None, None
        except Exception as e:
            if not error:
                error = []
            error.append(e)
            if self.exceptions:
                raise(e)
            rec, error = self.__next_valid__(error)
            return rec, error
        return rec, None

    def __next__(self):
        """Get next marc record."""
        self.error = ''
        try:
            rec = self._marc_reader.__next__()
        except StopIteration:
            return None, None, True
        except Exception as e:
            return None, e, False
            self.error = e
            if self.exceptions:
                raise(e)
        return rec, '', False

    def __iter__(self):
        """To support iteration."""
        rec, self.error, stop_iteration = self.__next__()
        while not stop_iteration:
            yield rec
            rec, self.error, stop_iteration = self.__next__()


# Records ---------------------------------------
class Records(pymarc.Record):
    """Represents Marc Records fetched from mrc file."""

    def __init__(
        self,
        mrc_file_name=None,
        exceptions=False
    ):
        """Constructor."""
        self._iterator = MrcIterator(mrc_file_name, exceptions)
        self.error = self._iterator.error

    def __iter__(self):
        """To support iteration."""
        for result in self._iterator:
            yield result

    def get_error(self):
        """Get error from iterator."""
        return self._iterator.error


# RecordsCount ---------------------------------------
class RecordsCount(Records):
    """Represents Marc Records fetched from mrc file with count."""

    def __init__(self,
                 mrc_file_name=None,
                 exceptions=True):
        """DocString."""
        super(RecordsCount, self).__init__(mrc_file_name)
        self.count = 0

    def __iter__(self):
        """To support iteration."""
        for result in self._iterator:
            self.count += 1
            yield result, self.count


# RecordsCountError ---------------------------------------
class RecordsCountError(RecordsCount):
    """Represents Marc Records fetched mrc file with count and error."""

    def __init__(
        self,
        mrc_file_name=None,
        exceptions=True
    ):
        """DocString."""
        super(RecordsCountError, self).__init__(mrc_file_name)

    def __iter__(self):
        """To support iteration."""
        for result, count in self._iterator:
            yield result, count, self._iterator.error
