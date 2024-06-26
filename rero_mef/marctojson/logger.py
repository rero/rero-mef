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

"""Marctojsons logger."""

# ---------------------------- Modules ----------------------------------------
import logging

__author__ = "Johnny Mariethoz <Johnny.Mariethoz@rero.ch>"
__version__ = "0.0.0"
__copyright__ = "Copyright (c) 2009-2011 Rero, Johnny Mariethoz"
__license__ = "Internal Use Only"


# LoggerError ----
class LoggerError:
    """Base class for errors in the Logger packages."""

    class InvalidileName(Exception):
        """The given file name is not correct."""


# Logger ---
class Logger:
    """To log several messages."""

    def __init__(
        self,
        name="VirtuaScript",
        log_output_file=None,
        log_console=True,
        log_level=logging.DEBUG,
        log_master=True,
    ):
        """
        Create an Looger object for messages logging.

        Keyword arguments:
        name  -- string : message application name
        log_output_file  -- string : name of the output file
        log_console  -- string : print message on the console
        log_level  -- logging.level : level of the log messages

        """
        self.name = name
        # create logger
        self.logger = logging.getLogger(name)
        if log_master:
            self.logger.setLevel(log_level)
            formatter = logging.Formatter(
                "%(id)9s" "\t%(levelname)8s" "\t%(error)25s" "\t%(message)s"
            )
            # create file handler logger
            if log_output_file is not None:
                try:
                    log_filehandler = logging.FileHandler(
                        log_output_file, mode="w", encoding="UTF-8"
                    )
                except IOError:
                    raise LoggerError.InvalidileName(
                        "Output file: %s cannot be " "created." % log_output_file
                    )
                log_filehandler.setFormatter(formatter)
                self.logger.addHandler(log_filehandler)
            # create console handler logger
            if log_console is True:
                log_console = logging.StreamHandler()
                log_console.setLevel(log_level)
                log_console.setFormatter(formatter)
                self.logger.addHandler(log_console)

    # close the logger
    def close(self):
        """Docstring."""
        handlers = self.logger.handlers[:]
        for handler in handlers:
            handler.close()
            self.logger.removeHandler(handler)

    # add id to logging
    def _log_id(self, lvl, id, error, message):
        """Docstring."""
        self.logger.log(lvl, message, extra={"id": id, "error": error})

    # with id---
    def debug_id(self, id, error, message):
        """Docstring."""
        self._log_id(logging.DEBUG, id, error, message)

    def info_id(self, id, error, message):
        """Docstring."""
        self._log_id(logging.INFO, id, error, message)

    def warning_id(self, id, error, message):
        """Docstring."""
        self._log_id(logging.WARNING, id, error, message)

    def error_id(self, id, error, message):
        """Docstring."""
        self._log_id(logging.ERROR, id, error, message)

    def critical_id(self, id, error, message):
        """Docstring."""
        self._log_id(logging.CRITICAL, id, error, message)

    # without id---
    def debug(self, error, message):
        """Docstring."""
        self.debug_id("", error, message)

    def info(self, error, message):
        """Docstring."""
        self.info_id("", error, message)

    def warning(self, error, message):
        """Docstring."""
        self.warning_id("", error, message)

    def error(self, error, message):
        """Docstring."""
        self.error_id("", error, message)

    def critical(self, error, message):
        """Docstring."""
        self.critical_id("", error, message)
