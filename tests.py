import codecs
from json import JSONEncoder
import json
from pmetro.model import load_map


class MapEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


def as_json(map_container):
    return json.dumps(map_container, ensure_ascii=False, indent=True, cls=MapEncoder)


with codecs.open('test.json','w') as f:
    f.write(as_json(load_map('TestMap', None)))