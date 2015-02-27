from pmetro.catalog_publishing import convert_map
from pmetro.log import ConsoleLog

convert_map({'id': '1',
             'city': '2',
             'iso': '3',
             'country': '4',
             'latitude': 5,
             'longitude': 6,
             'file': '7',
             'size': 8,
             'version': 9,
             'comments': None,
             'description': None,
             'map_id': '10'
            }, 'src', 'dst', ConsoleLog())