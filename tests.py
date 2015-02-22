from pmetro.catalog_publishing import convert_map
from pmetro.log import ConsoleLog


map_info = {"map_id": "Alexandria", "country": "Egypt", "file": "Alexandria.zip", "latitude": 31.21564, "longitude": 29.95527, "city": "Alexandria", "size": 2541, "version": 39947, "id": 361058, "description": "Схема от 18.06.2007г.\nАвтор: Варламов Дмитрий (www.chpeks.com)", "comments": None, "iso": "EG"}

convert_map(map_info, 'TestMap','TestMap.Converted', ConsoleLog())



