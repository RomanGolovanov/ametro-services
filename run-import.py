# /usr/bin/env python3
import datetime

from pmetro.catalog import MapCache, MapImporter
from settings import MAPS_SOURCE_URL, CACHE_PATH, TEMP_PATH, IMPORT_PATH, APP_LOG, FORCE_IMPORT

APP_LOG.message('')
APP_LOG.message('Publishing started at %s' % (datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')))

cache = MapCache(MAPS_SOURCE_URL, CACHE_PATH, TEMP_PATH, APP_LOG)
publication = MapImporter(IMPORT_PATH, TEMP_PATH, APP_LOG)
publication.import_maps(CACHE_PATH, force=FORCE_IMPORT)

APP_LOG.message('Publishing ended at %s' % (datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')))

