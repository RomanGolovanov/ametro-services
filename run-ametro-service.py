# /usr/bin/env python3

import os

from pmetro.catalog import MapCache, MapPublication
from pmetro.map import convert_map
from pmetro.vec2svg import UNKNOWN_COMMANDS, convert_vec_to_svg

base_dir = ''

cache_path = os.path.join(base_dir, 'cache')
publication_path = os.path.join(base_dir, 'www')
temp_path = os.path.join(base_dir, 'tmp')

pmetro_url = 'http://pub.skiif.org/pmetro-mirror/'

cache = MapCache(pmetro_url, cache_path)
cache.refresh()

publication = MapPublication(publication_path, temp_path)
publication.import_maps(cache_path)

#convert_map('MoscowMap', 'MoscowMap.converted')
#convert_vec_to_svg('TSaritsynoZhD.vec','TSaritsynoZhD.svg')

print('Unknown commands: ', UNKNOWN_COMMANDS)