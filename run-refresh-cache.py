# /usr/bin/env python3
import datetime

from publishing.downloader import MapDownloader
from settings import MAPS_SOURCE_URL, CACHE_PATH, TEMP_PATH, APP_LOG, FORCE_REFRESH

APP_LOG.message('')
APP_LOG.message('Importing started at %s' % (datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')))

cache = MapDownloader(MAPS_SOURCE_URL, CACHE_PATH, TEMP_PATH, APP_LOG)
cache.refresh(force=FORCE_REFRESH)

APP_LOG.message('Importing ended at %s' % (datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')))

