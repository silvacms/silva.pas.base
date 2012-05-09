# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest
from silva.pas.base.plugins.cookie import encode_query


class UtilsTestCase(unittest.TestCase):

    def test_encode(self):
        self.assertEqual(
            encode_query({}),
            '')
        self.assertEqual(
            encode_query({'option': 'value'}),
            '?option=value')
        self.assertEqual(
            encode_query({'option': u'peur ecclésiastique'}),
            '?option=peur+eccl%C3%A9siastique')
        self.assertEqual(
            encode_query({'option': [u'témeraire', 42, 'test']}),
            '?option=t%C3%A9meraire&option=42&option=test')
        self.assertEqual(
            encode_query({'option': 'x\xda\xd3`f``(\x01b\x86b\x10\xab\xbc\xb4\xbc\x98\x0bHg\xe6\xa5\x15%\xa6\xc6g\xa6Z\x02\x00R\x0b\x06\xd1'}),
            '?option=x%DA%D3%60f%60%60%28%01b%86b%10%AB%BC%B4%BC%98%0BHg%E6%A5%15%25%A6%C6g%A6Z%02%00R%0B%06%D1')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UtilsTestCase))
    return suite
