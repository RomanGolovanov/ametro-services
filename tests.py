from globalization.builder import build_geonames_database
from globalization.provider import GeoNamesProvider
from pmetro.log import ConsoleLog
from pmetro.pmz_import import convert_map

build_geonames_database('geonames', force=True)

# map_info = \
# {
#         'city': 'Amsterdam',
#         'comments': None,
#         'latitude': 52.37403,
#         'iso': 'NL',
#         'country': 'Netherlands',
#         'description': 'Схема от 17.12.2007г.',
#         'size': 25516,
#         'timestamp': 39947,
#         'map_id': 'Amsterdam',
#         'longitude': 4.88969,
#         'file': 'Amsterdam.zip',
#         'id': 2759794
#     }
#
# src = 'src'
# dst = 'dst'
# logger = ConsoleLog()
#
# convert_map(100500, 'Amsterdam.zip', 1301864400, src, dst, logger)
from pmetro.serialization import as_json

geonames_provider = GeoNamesProvider()

print(as_json(geonames_provider.get_names_for_language([614540], 'en')))
