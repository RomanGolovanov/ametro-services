# /usr/bin/env python3

from globalization.provider import GeoNamesProvider
from publishing.indexer import MapIndexer
from settings import APP_LOG, GEONAMES_DB, MANUAL_PATH, TEMP_PATH, PMETRO_PATH

geonames_provider = GeoNamesProvider(GEONAMES_DB)

APP_LOG.message('')

indexer = MapIndexer(MANUAL_PATH, PMETRO_PATH, TEMP_PATH, APP_LOG)
indexer.make_index()


