# /usr/bin/env python3
import datetime
from publishing.downloader import MapDownloader
from publishing.importer import MapImporter

from settings import MAPS_SOURCE_URL, CACHE_PATH, TEMP_PATH, IMPORT_PATH, APP_LOG, FORCE_IMPORT, FORCE_REFRESH

APP_LOG.message('')
APP_LOG.message('Synchronization started at %s' % (datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')))

cache = MapDownloader(MAPS_SOURCE_URL, CACHE_PATH, TEMP_PATH, APP_LOG)
cache.refresh(force=FORCE_REFRESH)

publication = MapImporter(IMPORT_PATH, TEMP_PATH, APP_LOG)
publication.import_maps(CACHE_PATH, force=FORCE_IMPORT)

APP_LOG.message('Synchronization ended at %s' % (datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')))

