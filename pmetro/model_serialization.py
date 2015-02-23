import codecs
from json import JSONEncoder
import json
import os


class MapEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


def as_json(obj):
    return json.dumps(obj, ensure_ascii=False, cls=MapEncoder)


def write_as_json_file(obj, path):
    with codecs.open(path, 'w', encoding='utf-8') as f:
        f.write(as_json(obj))


def store_model(map_container, dst_path):
    write_as_json_file(map_container.meta, os.path.join(dst_path, 'index.json'))

    for transport in map_container.transports:
        write_as_json_file(transport, os.path.join(dst_path, transport.name + '.transport.json'))

    for scheme in map_container.schemes:
        write_as_json_file(scheme, os.path.join(dst_path, scheme.name + '.scheme.json'))

