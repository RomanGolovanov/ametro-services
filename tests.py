from globalization.provider import GeoNamesProvider
from pmetro.log import ConsoleLog
from pmetro.pmz_import import convert_map
from settings import GEONAMES_DB


city_id = 498817
file = 'Bangalore.zip'
timestamp = 1242248400
map_folder = 'src'
converted_folder = 'dst'

convert_map(city_id, file, timestamp, map_folder, converted_folder, ConsoleLog(), GeoNamesProvider(GEONAMES_DB))
