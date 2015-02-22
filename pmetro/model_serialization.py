import codecs
from json import JSONEncoder
import json
import os


class MapEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


def as_json(map_container):
    return json.dumps(map_container, ensure_ascii=False, cls=MapEncoder)


def save_model(map_info, map_container, dst_path):
    with codecs.open(os.path.join(dst_path, 'city.json'), 'w', encoding='utf-8') as f:
        f.write(as_json(map_info))
    with codecs.open(os.path.join(dst_path, 'map.json'), 'w', encoding='utf-8') as f:
        f.write(as_json(map_container))

