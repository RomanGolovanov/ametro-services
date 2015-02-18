#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

from pmetro.catalog import MapCache, MapPublication
from pmetro.vec2svg import UNKNOWN_COMMANDS

base_dir = ''

cache_path = os.path.join(base_dir, 'cache')
publication_path = os.path.join(base_dir, 'www')
temp_path = os.path.join(base_dir, 'tmp')

pmetro_url = 'http://pmetro.chpeks.com/'

cache = MapCache(pmetro_url, cache_path)
cache.refresh()
publication = MapPublication(publication_path, temp_path)
publication.import_maps(cache_path)

print 'Unknown commands: %s' % UNKNOWN_COMMANDS