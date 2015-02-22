# /usr/bin/env python3
import datetime
import os

FORCE_UPDATE=False

from pmetro.catalog import MapCache, MapPublication
from pmetro.log import CompositeLog, LogLevel, ConsoleLog, FileLog

base_dir = ''

cache_path = os.path.join(base_dir, 'cache')
publication_path = os.path.join(base_dir, 'www')
temp_path = os.path.join(base_dir, 'tmp')

pmetro_url = 'http://pub.skiif.org/pmetro-mirror/'

log = CompositeLog([
    ConsoleLog(level=LogLevel.Info),
    FileLog(file_path='import.verbose.log', level=LogLevel.Debug),
    FileLog(file_path='import.log', level=LogLevel.Warning)
])

log.info('Synchronization started at %s' % (datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')))

#cache = MapCache(pmetro_url, cache_path, temp_path, log)
#cache.refresh(force=FORCE_UPDATE)

publication = MapPublication(publication_path, temp_path, log)
publication.import_maps(cache_path, force=FORCE_UPDATE)

log.info('Synchronization ended at %s' % (datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')))

