import codecs
from json import JSONEncoder
import json
import os


class MapEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


def as_json(map_container):
    return json.dumps(map_container, ensure_ascii=False, cls=MapEncoder, indent=4)


def store_model(map_container, dst_path):
    with codecs.open(os.path.join(dst_path, 'meta.json'), 'w', encoding='utf-8') as f:
        f.write(as_json(map_container.meta))
    with codecs.open(os.path.join(dst_path, 'main.json'), 'w', encoding='utf-8') as f:
        f.write(as_json(map_container))

