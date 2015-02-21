# /usr/bin/env python3

import os

from pmetro.catalog import MapCache, MapPublication
from pmetro.log import CompositeLog, LogLevel, ConsoleLog, FileLog
from pmetro.map import convert_map
from pmetro.vec2svg import convert_vec_to_svg

base_dir = ''

cache_path = os.path.join(base_dir, 'cache')
publication_path = os.path.join(base_dir, 'www')
temp_path = os.path.join(base_dir, 'tmp')

pmetro_url = 'http://pub.skiif.org/pmetro-mirror/'

log = CompositeLog([
    ConsoleLog(level=LogLevel.Info),
    FileLog(file_path='import.log', level=LogLevel.Debug)
])

# cache = MapCache(pmetro_url, cache_path, log)
#cache.refresh()

#publication = MapPublication(publication_path, temp_path, log)
#publication.import_maps(cache_path)

convert_map('TestMap', 'TestMapConverted', ConsoleLog())

# for f in [x for x in os.listdir('.') if x.endswith('vec')]:
#     print('Convert file %s' % f)
#     convert_vec_to_svg(f, f[:-4] + '.svg', ConsoleLog())

