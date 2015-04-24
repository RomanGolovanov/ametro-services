# /usr/bin/env python3
import datetime
from globalization.provider import GeoNamesProvider
from publishing.downloader import MapDownloader
from publishing.importer import MapImporter
from settings import MAPS_SOURCE_URL, CACHE_PATH, TEMP_PATH, IMPORT_PATH, APP_LOG, FORCE_IMPORT, GEONAMES_DB

geonames_provider = GeoNamesProvider(GEONAMES_DB)

APP_LOG.message('')
APP_LOG.message('Publishing started at %s' % (datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')))

cache = MapDownloader(MAPS_SOURCE_URL, CACHE_PATH, TEMP_PATH, APP_LOG, geonames_provider)
publication = MapImporter(IMPORT_PATH, TEMP_PATH, APP_LOG, geonames_provider)
publication.import_maps(CACHE_PATH, force=FORCE_IMPORT)

APP_LOG.message('Publishing ended at %s' % (datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')))

