from pmetro import model_serialization
from pmetro.catalog_publishing import convert_map
from pmetro.importers.importer import PmzImporter
from pmetro.log import ConsoleLog

map_info = \
    {
        'city': 'Amsterdam',
        'comments': None,
        'latitude': 52.37403,
        'iso': 'NL',
        'country': 'Netherlands',
        'description': 'Схема от 17.12.2007г.',
        'size': 25516,
        'version': 39947,
        'map_id': 'Amsterdam',
        'longitude': 4.88969,
        'file': 'Amsterdam.zip',
        'id': 2759794
    }

src = 'src'
dst = 'dst'
logger = ConsoleLog()

importer = PmzImporter(src, map_info)
container = importer.import_pmz()

print(model_serialization.as_json(container))

convert_map(map_info, src, dst, logger)