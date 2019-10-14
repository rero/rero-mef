#!/usr/bin/env bash
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

# COLORS for messages
NC='\033[0m'                    # Default color
INFO_COLOR='\033[1;97;44m'      # Bold + white + blue background
SUCCESS_COLOR='\033[1;97;42m'   # Bold + white + green background
ERROR_COLOR='\033[1;97;41m'     # Bold + white + red background

PROGRAM=`basename $0`

# MESSAGES
msg() {
  echo -e "${1}" 1>&2
}
# Display a colored message
# More info: https://misc.flogisoft.com/bash/tip_colors_and_formatting
# $1: choosen color
# $2: title
# $3: the message
colored_msg() {
  msg "${1}[${2}]: ${3}${NC}"
}

info_msg() {
  colored_msg "${INFO_COLOR}" "INFO" "${1}"
}

error_msg() {
  colored_msg "${ERROR_COLOR}" "ERROR" "${1}"
}

error_msg+exit() {
    error_msg "${1}" && exit 1
}

success_msg() {
  colored_msg "${SUCCESS_COLOR}" "SUCCESS" "${1}"
}

# Displays program name
msg "PROGRAM: ${PROGRAM}"


set -e

info_msg "Pipenv check:"
pipenv check
info_msg "Test pydocstyle:"
pipenv run pydocstyle rero_mef tests docs
info_msg "Test isort:"
pipenv run isort -rc -c -df
info_msg "Test useless imports:"
pipenv run autoflake -c -r --remove-all-unused-imports --exclude ui --ignore-init-module-imports . &> /dev/null || \
  error_msg+exit "\nUse this command to check imports: \n\tautoflake --remove-all-unused-imports -r --exclude ui --ignore-init-module-imports .\n"
info_msg "Check-manifest:"
pipenv run check-manifest --ignore ".travis-*,docs/_build*"
info_msg "Sphinx-build:"
pipenv run sphinx-build -qnNW docs docs/_build/html
info_msg "Tests:"
pipenv run test

success_msg "Perfect ${PROGRAM}! See you soon…"
exit 0
