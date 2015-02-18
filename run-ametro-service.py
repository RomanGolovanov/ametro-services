#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from pmetro.map import convert_vec_to_svg, convert_map
from pmetro.catalog import MapCache, MapPublication
from pmetro.vec2svg import UNKNOWN_COMMANDS

base_dir = ''

cache_path = os.path.join(base_dir, 'cache')
publication_path = os.path.join(base_dir, 'www')
temp_path = os.path.join(base_dir, 'tmp')

pmetro_url = 'http://pmetro.chpeks.com/'

#cache = MapCache(pmetro_url, cache_path)
#cache.refresh()

#publication = MapPublication(publication_path, temp_path)
#publication.import_maps(cache_path)


#convert_vec_to_svg('Borovitskaya.vec','Borovitskaya.svg')
#convert_vec_to_svg('Aeroport.vec','Aeroport.svg')
#convert_vec_to_svg('Tretyakovskaya.vec','Tretyakovskaya.svg')

print 'Unknown commands: %s' % UNKNOWN_COMMANDS

convert_map('MoscowMap', 'MoscowMap.converted')

print 'Unknown commands: %s' % UNKNOWN_COMMANDS