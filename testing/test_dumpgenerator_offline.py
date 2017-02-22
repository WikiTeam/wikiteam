#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   This file is part of the wikiteam project.
#
#   Copyright (C) 2017 Robert Felten - https://github.com/rfelten/
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software Foundation,
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # q&d import hack, sorry
import unittest
from dumpgenerator import truncateFilename

# This file is intended to test offline functionality of the dumpgenerator.py.
# For all other tests see test_dumpgenerator.py


class TestDumpgeneratorOffline(unittest.TestCase):

    def setUp(self):
        other = dict()  # FIXME: get from dumpgenerator, but code base is a pre-OO mess
        other['filenamelimit'] = 100

        self.other = other

    def tearDown(self):
        pass

    def helper_truncateFilename(self, fn):
        fn_trunc = truncateFilename(other=self.other, filename=fn)
        self.assertLessEqual(len(fn_trunc), self.other['filenamelimit'],
                             "trunced filename '%s' len of %d exceed limit of %d." % (
                             fn_trunc, len(fn_trunc), self.other['filenamelimit']))

    def test_truncateFilename1(self):
        """ Test if truncFilename() obey other['filenamelimit'] - real world example 1"""
        fn = u"Assortiment de différentes préparation à bases de légumes et féculents, bien sur servit avec de l'injara.JPG"
        self.assertEqual(len(fn), 108)
        self.assertEqual(len(fn.encode("utf-8")), 113)  # chars like 'è' will extend length - this is maybe unexpected
        self.helper_truncateFilename(fn)

    def test_truncateFilename2(self):
        """ Test if truncFilename() obey other['filenamelimit'] - longest valid name w/o file extension"""
        fn = "A" * self.other['filenamelimit']
        self.helper_truncateFilename(fn)

    def test_truncateFilename3(self):
        """ Test if truncFilename() obey other['filenamelimit'] - longest valid name w/ file extension"""
        fn = "A" * self.other['filenamelimit']
        fn = fn[:-4] + ".jpg"
        self.helper_truncateFilename(fn)

    def test_truncateFilename4(self):
        """ Test if truncFilename() obey other['filenamelimit'] - longest valid name w/ file extension"""
        fn = "A" * (self.other['filenamelimit'] / 2)
        fn = fn[:-4] + ".jpg"
        self.helper_truncateFilename(fn)


if __name__ == '__main__':
    unittest.main()
