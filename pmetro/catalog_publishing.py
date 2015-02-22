import os

from PIL import Image

from pmetro.log import EmptyLog
from pmetro.model_import import import_pmz_map
from pmetro.model_serialization import save_model
from pmetro.vec2svg import convert_vec_to_svg


def convert_map(map_info, src_path, dst_path, log=EmptyLog()):
    if not os.path.isdir(dst_path):
        os.mkdir(dst_path)

    map_container = import_pmz_map(src_path)
    save_model(map_info, map_container, dst_path)
    convert_static_files(dst_path, src_path, log)


def convert_static_files(dst_path, src_path, log=EmptyLog()):
    file_converters = {
        'vec': (convert_vec_to_svg, 'svg'),
        'bmp': (lambda src, dst, l: Image.open(src).save(dst), 'png'),
        'gif': (lambda src, dst, l: Image.open(src).save(dst), 'png')
    }
    map_files = os.listdir(src_path)
    for src_name in map_files:
        src_file_path = os.path.join(src_path, src_name)

        if not (os.path.isfile(src_file_path)):
            continue

        src_file_ext = src_file_path[-3:]
        if src_file_ext in file_converters:
            dst_file_path = os.path.join(dst_path, src_name[:-3] + file_converters[src_file_ext][1])
            log.debug('Convert %s' % src_file_path)
            file_converters[src_file_ext][0](src_file_path, dst_file_path, log)

