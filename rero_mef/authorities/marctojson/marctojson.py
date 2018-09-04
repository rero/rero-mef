#!/usr/bin/env python
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

"""Marctojson main script."""

import argparse
import json
import logging
import os
import sys
from datetime import datetime

from helper import file_name
from logger import Logger
from mef_record import MEF_record
from records import RecordsCount

if __name__ == '__main__':

    sys.stdout = \
        open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)

    usage = "usage: %prog bibfile [options]"

    parser = argparse.ArgumentParser(
        description="Exclude bibs from marc file"
    )

    parser.add_argument(dest="marc_file",
                        help="Marc file to transform")

    parser.add_argument(dest="transformation",
                        help="transformation name")

    parser.add_argument("-v", "--verbose", dest="verbose",
                        help="Verbose mode",
                        action="store_true", default=False)

    parser.add_argument("-l", "--logpath", dest="logpath",
                        help="logpath",
                        default='.')

    parser.add_argument("-o", "--output", dest="output",
                        help="output file name",
                        default=None)

    parser.add_argument("-m", "--md5", dest="md5",
                        help="calculate the JSON MD5 hash value and " +
                        "add it to the JSON",
                        action="store_true", default=False)

    options = parser.parse_args()


# ---
    script_name = file_name(__file__)

    file_prefix = script_name + '_' + \
        datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')

    log_output_file = options.logpath + '/' + file_prefix + '.log'

    file_logger = Logger(
        name=script_name + ":file",
        log_output_file=log_output_file, log_console=options.verbose,
        log_level=logging.INFO
    )

    machine_name = os.uname()[1]
    file_logger.info("Starting script:", "%s on %s" % (__file__, machine_name))
    file_logger.info("Transformation:", options.transformation)
    file_logger.info("Open file:", options.marc_file)
    json_file = None
    if options.output:
        json_file = open(options.output, 'w', encoding='utf8')
        file_logger.info("Json file:", options.output)

    try:
        records = RecordsCount(options.marc_file)
    except Exception as e:
        file_logger.error("Marc file not fount:", options.marc_file)
        file_logger.error("", e.msg)
        file_logger.info(
            "End of script:", "%s on %s" % (__file__, machine_name)
        )
        sys.exit(1)

    # try:
    module_name = options.transformation
    module = __import__(module_name, fromlist=[''])
    Transformation = getattr(module, 'Transformation')

    file_logger.info("Start", "---")
    if json_file:
        json_file.write('[\n')
    else:
        print('[')
    for record, count in records:
        if count > 1:
            if json_file:
                json_file.write(',\n')
            else:
                print(',')

        # do tranformation
        data = Transformation(
            marc=record,
            logger=file_logger,
            verbose=options.verbose
        )
        if options.md5:
            MEF_record.add_md5_to_json(json_data=data.json)
        if json_file:
            json.dump(data.json, json_file, ensure_ascii=False, indent=2)
        else:
            print(json.dumps(data.json, ensure_ascii=False, indent=2), end='')

    # except Exception as e:
    #     file_logger.error(
    #         "Transformation not fount:", options.transformation
    #     )

    if json_file:
        json_file.write('\n]\n')
        json_file.close()
    else:
        print(']')

    file_logger.info("End of script:", "%s on %s" % (__file__, machine_name))
    sys.exit(0)
