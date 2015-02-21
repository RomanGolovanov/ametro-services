import os
import shutil
from PIL import Image

from pmetro.files import read_all_lines
from pmetro.log import EmptyLog
from pmetro.vec2svg import convert_vec_to_svg


def convert_map(src_path, dst_path, log=EmptyLog()):
    if not os.path.isdir(dst_path):
        os.mkdir(dst_path)

    convert_map_database(src_path, dst_path, log)
    convert_files(dst_path, src_path, log)


def convert_files(dst_path, src_path, log=EmptyLog()):
    file_converters = {
        'vec': (convert_vec_to_svg, 'svg'),
        'bmp': (convert_bmp_to_png, 'png')
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
        else:
            dst_file_path = os.path.join(dst_path, src_name)
            log.debug('Copy %s' % src_file_path)
            shutil.copy(src_file_path, dst_file_path)


def convert_bmp_to_png(src_path, dst_path, log=EmptyLog()):
    Image.open(src_path).save(dst_path)


def convert_map_database(src_path, dst_path, log=EmptyLog()):
    txt_files = sorted([f for f in os.listdir(src_path) if f.lower().endswith('.txt')])

    for file_path in map(lambda x: os.path.join(src_path, x), txt_files):
        convert_to_json(read_all_lines(file_path))


def convert_to_json(lines):
    section = None
    for line in map(lambda x: x.strip().replace('\\n', '\n'), lines):
        if line is None or line.startswith(';'):
            continue
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1]








