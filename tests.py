from pmetro.log import ConsoleLog
from pmetro.pmz_import import convert_map


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

convert_map(map_info, src, dst, logger)