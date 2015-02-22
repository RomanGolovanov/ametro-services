import codecs
from pmetro.model_import import import_pmz_map
from pmetro.model_serialization import as_json


# with codecs.open('test.json','w') as f:
#     f.write(as_json(import_pmz_map('TestMap')))
from pmetro.model_transports import __get_stations


