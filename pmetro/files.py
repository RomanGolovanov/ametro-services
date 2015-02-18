# -*- coding: utf-8 -*-


import codecs
import shutil
import os
import zipfile


def unzip_file(source_filename, destination_path):
    with zipfile.ZipFile(source_filename) as zf:
        zf.extractall(destination_path)
        zf.close()


def zip_folder(source_path, destination_filename):
    tmp_file_path = os.path.join(os.path.dirname(source_path), 'archive')

    shutil.make_archive(tmp_file_path, 'zip', source_path)

    if os.path.isfile(destination_filename):
        os.remove(destination_filename)

    os.rename(tmp_file_path + '.zip', destination_filename)


def find_file_by_extension(path, file_ext):
    file_ext = file_ext.lower()
    for file_name in os.listdir(path):
        if file_name.lower().endswith(file_ext):
            return os.path.join(path, file_name)


def convert_to_utf(source_file_path, target_file_path):
    source_formats = ['windows-1251', 'iso-8859-1', 'ascii']
    target_format = 'utf-8'
    for source_format in source_formats:
        try:
            with codecs.open(source_file_path, 'rU', source_format) as source_file:
                with codecs.open(target_file_path, 'w', target_format) as target_file:
                    for line in source_file:
                        target_file.write(unicode(line))
            return target_file_path
        except UnicodeDecodeError:
            pass

    raise IOError("Error: failed to convert '" + source_file_path + "' to UTF8.")


def read_all_lines(source_file_path):
    source_formats = ['windows-1251', 'iso-8859-1', 'ascii']
    for source_format in source_formats:
        try:
            lines = []
            with codecs.open(source_file_path, 'rU', source_format) as source_file:
                for line in source_file:
                    lines.append(unicode(line))
            return lines
        except UnicodeDecodeError:
            pass

    raise IOError("Error: failed to read all lines from '" + source_file_path + "'.")