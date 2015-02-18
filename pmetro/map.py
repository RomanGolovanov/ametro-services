# -*- coding: utf-8 -*-
import os
import shutil
from pmetro.readers import IniReader

from pmetro.vec2svg import convert_vec_to_svg


def convert_map(src_path, dst_path):
    if not os.path.isdir(dst_path):
        os.mkdir(dst_path)

    file_converters = {
        'txt': (convert_txt_to_json, 'json'),
        # 'vec': (convert_vec_to_svg, 'svg'),
        'bmp': (__copy_file, 'bmp')
    }

    map_files = os.listdir(src_path)

    for src_name in map_files:
        src_file_path = os.path.join(src_path, src_name)
        if not (os.path.isfile(src_file_path)):
            continue

        src_file_ext = src_file_path[-3:]
        if src_file_ext in file_converters:
            dst_file_path = os.path.join(dst_path, src_name[:-3] + file_converters[src_file_ext][1])
            file_converters[src_file_ext][0](src_file_path, dst_file_path)


def __copy_file(src_file_path, dst_file_path):
    shutil.copy(src_file_path, dst_file_path)


def convert_txt_to_json(src_file_path, dst_file_path):
    ini = IniReader()
    ini.open(src_file_path, 'windows-1251')
    ini.section(u'Options')

    indent = ''
    caption = '-'

    while ini.read():
        name = ini.name().strip()
        if name == u'caption':
            caption = ini.value()
        if name == u'StringToAdd'.lower():
            indent = ini.value().strip('\'').strip()

    print '%s%s' % (indent, caption)
