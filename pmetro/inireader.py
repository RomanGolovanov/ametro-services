#!/usr/bin/python
# -*- coding: utf-8 -*-

import codecs


class inireader:
    def __init__(self):
        self.lines = []
        self.position = None

    def open(self, path, encoding):
        f = codecs.open(path, "r", encoding = encoding)
        self.lines = f.readlines()
        self.position = 0

    def section(self, section):
        index = 0;
        pattern = u'[' + section + u']'
        while index < len(self.lines):
            if str(self.lines[index]).strip().lower() == str(pattern).lower():
                self.position = index
                return
            index += 1
        raise 'No section ' + section + ' found'

    def read(self):
        if self.position is None:
            self.position = 0
        else:
            self.position += 1

        if self.position >= len(self.lines):
            return False

        line = self.lines[self.position].strip()
        if line.startswith('[') and line.endswith(']'):
            return False

        return True

    def name(self):
        return self.lines[self.position].strip().lower().split(u'=')[0]

    def value(self):
        return self.lines[self.position].strip().split(u'=')[1]


