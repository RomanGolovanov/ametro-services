import codecs
from json import JSONEncoder
import json
import os


class MapEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


def as_json(obj):
    return json.dumps(obj, ensure_ascii=False, cls=MapEncoder, indent=4)


def write_as_json_file(obj, path):
    with codecs.open(path, 'w', encoding='utf-8') as f:
        f.write(as_json(obj))


def store_model(map_container, dst_path):
    write_as_json_file(map_container.meta, os.path.join(dst_path, 'index.json'))
    write_as_json_file(map_container.images, os.path.join(dst_path, 'images.json'))

    transports_path = os.path.join(dst_path, 'transports')
    if not os.path.isdir(transports_path):
        os.mkdir(transports_path)

    for transport in map_container.transports:
        write_as_json_file(transport, os.path.join(transports_path, transport.name + '.json'))

    schemes_path = os.path.join(dst_path, 'schemes')
    if not os.path.isdir(schemes_path):
        os.mkdir(schemes_path)

    for scheme in map_container.schemes:
        write_as_json_file(scheme, os.path.join(schemes_path, scheme.name + '.json'))


