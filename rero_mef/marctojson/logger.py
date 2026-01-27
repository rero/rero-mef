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

    class InvalidNameError(Exception):
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
        """Create a Logger object for messages logging.

        :param name: Message application name.
        :param log_output_file: Name of the output file.
        :param log_console: If True, print messages on the console.
        :param log_level: Level of the log messages (default: logging.DEBUG).
        :param log_master: If True, set as master logger.
        :raises LoggerError.InvalidNameError: If ``log_output_file`` cannot be created.
        """
        self.name = name
        # create logger
        self.logger = logging.getLogger(name)
        if log_master:
            self.logger.setLevel(log_level)
            formatter = logging.Formatter(
                "%(id)9s\t%(levelname)8s\t%(error)25s\t%(message)s"
            )
            # create file handler logger
            if log_output_file is not None:
                try:
                    log_filehandler = logging.FileHandler(
                        log_output_file, mode="w", encoding="UTF-8"
                    )
                except OSError:
                    raise LoggerError.InvalidNameError(
                        f"Output file: {log_output_file} cannot be created."
                    )
                log_filehandler.setFormatter(formatter)
                self.logger.addHandler(log_filehandler)
            # create console handler logger
            if log_console is True:
                log_console = logging.StreamHandler()
                log_console.setLevel(log_level)
                log_console.setFormatter(formatter)
                self.logger.addHandler(log_console)

    def close(self):
        """Close all handlers and remove them from the logger."""
        handlers = self.logger.handlers[:]
        for handler in handlers:
            handler.close()
            self.logger.removeHandler(handler)

    def _log_id(self, lvl, id_, error, message):
        """Emit a log record with an identifier and error context.

        :param lvl: Logging level (e.g. ``logging.DEBUG``).
        :param id_: Record identifier included in the log output.
        :param error: Error context string included in the log output.
        :param message: Log message body.
        """
        self.logger.log(lvl, message, extra={"id": id_, "error": error})

    def debug_id(self, id_, error, message):
        """Log a DEBUG message with a record identifier.

        :param id_: Record identifier.
        :param error: Error context string.
        :param message: Log message body.
        """
        self._log_id(logging.DEBUG, id_, error, message)

    def info_id(self, id_, error, message):
        """Log an INFO message with a record identifier.

        :param id_: Record identifier.
        :param error: Error context string.
        :param message: Log message body.
        """
        self._log_id(logging.INFO, id_, error, message)

    def warning_id(self, id_, error, message):
        """Log a WARNING message with a record identifier.

        :param id_: Record identifier.
        :param error: Error context string.
        :param message: Log message body.
        """
        self._log_id(logging.WARNING, id_, error, message)

    def error_id(self, id_, error, message):
        """Log an ERROR message with a record identifier.

        :param id_: Record identifier.
        :param error: Error context string.
        :param message: Log message body.
        """
        self._log_id(logging.ERROR, id_, error, message)

    def critical_id(self, id_, error, message):
        """Log a CRITICAL message with a record identifier.

        :param id_: Record identifier.
        :param error: Error context string.
        :param message: Log message body.
        """
        self._log_id(logging.CRITICAL, id_, error, message)

    def debug(self, error, message):
        """Log a DEBUG message without a record identifier.

        :param error: Error context string.
        :param message: Log message body.
        """
        self.debug_id("", error, message)

    def info(self, error, message):
        """Log an INFO message without a record identifier.

        :param error: Error context string.
        :param message: Log message body.
        """
        self.info_id("", error, message)

    def warning(self, error, message):
        """Log a WARNING message without a record identifier.

        :param error: Error context string.
        :param message: Log message body.
        """
        self.warning_id("", error, message)

    def error(self, error, message):
        """Log an ERROR message without a record identifier.

        :param error: Error context string.
        :param message: Log message body.
        """
        self.error_id("", error, message)

    def critical(self, error, message):
        """Log a CRITICAL message without a record identifier.

        :param error: Error context string.
        :param message: Log message body.
        """
        self.critical_id("", error, message)
