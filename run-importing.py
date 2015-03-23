# /usr/bin/env python3
import datetime
import os

from globalization.builder import build_geonames_database
from pmetro import ini_files
from pmetro import pmz_transports
from pmetro.catalog import MapCache
from pmetro.log import CompositeLog, LogLevel, ConsoleLog, FileLog


base_dir = ''

cache_path = os.path.join(base_dir, 'cache')
publication_path = os.path.join(base_dir, 'www')
temp_path = os.path.join(base_dir, 'tmp')

build_geonames_database('geonames')

pmetro_url = 'http://pub.skiif.org/pmetro-mirror/'

log = CompositeLog([
    ConsoleLog(level=LogLevel.Info),
    FileLog(file_path='import.verbose.log', level=LogLevel.Debug),
    FileLog(file_path='import.warnings.log', level=LogLevel.Warning),
    FileLog(file_path='import.errors.log', level=LogLevel.Error)
])

ini_files.LOG = log
pmz_transports.LOG = log

log.message('')
log.message('Importing started at %s' % (datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')))

cache = MapCache(pmetro_url, cache_path, temp_path, log)
cache.refresh(force=False)

log.message('Importing ended at %s' % (datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')))

