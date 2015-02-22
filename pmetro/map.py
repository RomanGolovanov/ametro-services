import codecs
from json import JSONEncoder
import json
import os

from PIL import Image

from pmetro.log import EmptyLog
from pmetro.model import load_map
from pmetro.vec2svg import convert_vec_to_svg

__IGNORED_FILE_TYPES = ['pm3d', 'pms']


class MapEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


def as_json(map_container):
    return json.dumps(map_container, ensure_ascii=False, indent=False, cls=MapEncoder)


def convert_map(map_info, src_path, dst_path, log=EmptyLog()):
    if not os.path.isdir(dst_path):
        os.mkdir(dst_path)

    with codecs.open(os.path.join(dst_path, 'city.json'), 'w', encoding='utf-8') as f:
        f.write(as_json(map_info))

    convert_metadata(src_path, dst_path, log)
    convert_descriptions(src_path, dst_path, log)
    convert_static_files(dst_path, src_path, log)


def convert_metadata(src_path, dst_path, log):
    with codecs.open(os.path.join(dst_path, 'map.json'), 'w', encoding='utf-8') as f:
        f.write(as_json(load_map(src_path)))


def convert_descriptions(src_path, dst_path, log=EmptyLog()):
    txt_files = sorted([f for f in os.listdir(src_path) if f.lower().endswith('.txt')])


def convert_static_files(dst_path, src_path, log=EmptyLog()):
    file_converters = {
        'vec': (convert_vec_to_svg, 'svg'),
        'bmp': (lambda src, dst, log: Image.open(src).save(dst), 'png'),
        'gif': (lambda src, dst, log: Image.open(src).save(dst), 'png')
    }
    map_files = os.listdir(src_path)
    for src_name in map_files:
        src_file_path = os.path.join(src_path, src_name)

        if any([x for x in __IGNORED_FILE_TYPES if src_name.endswith(x)]):
            log.debug('Ignore %s' % src_file_path)
            continue

        if not (os.path.isfile(src_file_path)):
            continue

        src_file_ext = src_file_path[-3:]
        if src_file_ext in file_converters:
            dst_file_path = os.path.join(dst_path, src_name[:-3] + file_converters[src_file_ext][1])
            log.debug('Convert %s' % src_file_path)
            file_converters[src_file_ext][0](src_file_path, dst_file_path, log)
        else:
            log.debug('Unknown type of file %s' % src_file_path)

