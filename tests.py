from globalization.provider import GeoNamesProvider
from pmetro.log import ConsoleLog
from pmetro.pmz_import import convert_map

# build_geonames_database(force=True)

# map_info = \
#     {
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

cities = geonames_provider.get_cities_info([325363, 3469058, 1508291])

#print(as_json(cities ))



print(as_json(geonames_provider.get_names_for_language([c.geoname_id for c in cities], 'en')))
print(as_json(geonames_provider.get_names_for_language([c.geoname_id for c in cities], 'ru')))
