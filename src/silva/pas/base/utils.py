# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import urllib


def encode_query(query):
    results = []

    def encode_value(key, value):
        if isinstance(value, basestring):
            if isinstance(value, unicode):
                try:
                    value = value.encode('utf-8')
                except UnicodeEncodeError:
                    pass
        elif isinstance(value, (list, tuple)):
            for item in value:
                encode_value(key, item)
            return
        else:
            try:
                value = str(value)
            except:
                pass
        results.append((key, value))

    for key, value in query.items():
        encode_value(key, value)

    if results:
        return '?' + urllib.urlencode(results)
    return ''
