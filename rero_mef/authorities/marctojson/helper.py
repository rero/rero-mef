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

"""Helper."""
import copy
import os
import re

# ---------------------------- Modules ----------------------------------------

__author__ = "Peter Weber <Peter.Weber@rero.ch>"
__version__ = "0.0.0"
__copyright__ = "Copyright (c) 2009-2011 Rero, Johnny Mariethoz"
__license__ = "Internal Use Only"


# ---------------------------- Functions --------------------------------------
def file_name(file_name):
    """Gets the filename without extention."""
    return '.'.join(os.path.basename(file_name).split('.')[:-1])


def replace_ctrl(text):
    """Replaces control characters with symbols."""
    newtext = u''
    for c in text:
        if ord(c) <= 0x20:
            c = chr(0x2400 + ord(c))
        # stopwords
        if ord(c) == 0x9C:
            c = '|'
        newtext += c
    # text = text.replace('\n', u'␊')
    # text = text.replace('\r', u'␍')
    # text = text.replace('\t', u'␉')
    # text = text.replace( ' ', u'␠')
    return newtext


def nice_field(field, ctrl=False, tab=False):
    """Changes marc 21 strings to more visible strings 1Fa -> $a with tag."""
    res = ''
    try:
        if tab:
            res = 'tag[%s]\t%s' % \
                (field.tag, nice_marc_field(field, ctrl, tab))
        else:
            res = 'tag[%s] %s' % \
                (field.tag, nice_marc_field(field, ctrl, tab))
    except Exception as e:
        pass
    return res


def nice_marc_field(field, ctrl=False, tab=False):
    """Changes marc 21 strings to more visible strings 1Fa -> $a."""
    res = ''
    field = copy.deepcopy(field)
    try:
        if field.is_control_field():
            if ctrl:
                data = replace_ctrl(field.data)
            else:
                data = field.data
            if tab:
                res = '  \t' + data
            else:
                res = '   ' + data
        else:
            res = ''
            # make indicator 1 nicer
            if field.indicator1 != ' ':
                res = field.indicator1
            else:
                res = '_'
            # make indicator 2 nicer
            if field.indicator2 != ' ':
                res += field.indicator2
            else:
                res += '_'
            # make subfields nicer
            for subfield in field:
                sub_data = subfield[1]
                if ctrl:
                    if tab:
                        res += '\t$' + subfield[0] + '\t' \
                            + replace_ctrl(sub_data)
                    else:
                        res += ' $' + subfield[0] + ' ' \
                            + replace_ctrl(sub_data)
                else:
                    if subfield[0] == '6':
                        sub_data = "%-9s" % sub_data
                    if tab:
                        res += '\t$' + subfield[0] + '\t' + sub_data
                    else:
                        res += ' $' + subfield[0] + ' ' + sub_data
    except Exception as e:
        pass
    return res


def nice_record(record, ctrl=False):
    """Make nice marc record."""
    nice = ''
    for field in record:
        nice += '%s: %s' % (field.tag, nice_marc_field(field, ctrl)) + '\n'
    return nice


def display_record(record, ctrl=False):
    """Displays the record pymarc like."""
    print(nice_record(record, ctrl))


def remove_trailing_punctuation(data, punctuation=',',
                                spaced_punctuation=':;/-'):
    """Remove trailing punctuation from data.

    The punctuation parameter list the
    punctuation characters to be removed
    (preceded by a space or not).

    The spaced_punctuation parameter list the
    punctuation characters needing one or more preceding space(s)
    in order to be removed.
    """
    return re.sub(
        r'([{0}]|\s+[{1}])$'.format(punctuation, spaced_punctuation),
        '',
        data.rstrip()
    ).rstrip()


def build_string_list_from_fields(record, tag, subfields):
    """Build a list of strings (one per field).

    from the given field tag and given subfields.
    the given separator is used as subfields delimitor.
    """
    fields = record.get_fields(tag)
    field_string_list = []
    for field in fields:
        subfield_string = ''
        for code, data in field:
            if code in subfields:
                if isinstance(data, (list, set)):
                    data = subfields[code].join(data)
                data = data.replace('\x98', '')
                data = data.replace('\x9C', '')
                data = data.replace(',,', ',')
                data = remove_trailing_punctuation(data)
                data = data.strip()
                if subfield_string != '':
                    subfield_string += subfields[code] + data
                else:
                    subfield_string += data
        field_string_list.append(subfield_string)
    return field_string_list


def as_marc(field):
    """Docstring."""
    return field.as_marc(encoding='utf-8').decode('utf-8')


def has_roman_number(string, befor='', after=''):
        """Find all roman numbers in string before.

        string befor roman numbers after: string behind roman number.
        """
        re_roman_number = re.compile(
            r'(' +
            befor +
            r'M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})' +
            after +
            r')')
        roman_numbers = re_roman_number.findall(string)
        res = []
        for roman_number in roman_numbers:
            if roman_number:
                res.append(roman_number)
        return res
