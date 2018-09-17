# /usr/bin/env python3
import datetime
from globalization.provider import GeoNamesProvider
from publishing.downloader import MapDownloader
from publishing.importer import MapImporter
from publishing.indexer import MapIndexer
from publishing.publisher import publish_maps
from settings import MAPS_SOURCE_URL, CACHE_PATH, TEMP_PATH, IMPORT_PATH, APP_LOG, FORCE_IMPORT, GEONAMES_DB, \
    FORCE_REFRESH, PUBLISHING_PATH, GEONAMES_DB, MANUAL_PATH, PMETRO_PATH

geonames_provider = GeoNamesProvider(GEONAMES_DB)

APP_LOG.message('')
APP_LOG.message('Publishing started at %s' % (datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')))

indexer = MapIndexer(MANUAL_PATH, PMETRO_PATH, TEMP_PATH, APP_LOG)
indexer.make_index()

cache = MapDownloader(MAPS_SOURCE_URL, CACHE_PATH, TEMP_PATH, APP_LOG, geonames_provider)
cache.refresh(force=FORCE_REFRESH)

publication = MapImporter(IMPORT_PATH, TEMP_PATH, APP_LOG, geonames_provider)
publication.import_maps(CACHE_PATH, force=FORCE_IMPORT)

publish_maps(IMPORT_PATH, PUBLISHING_PATH, geonames_provider)

APP_LOG.message('Publishing ended at %s' % (datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')))

