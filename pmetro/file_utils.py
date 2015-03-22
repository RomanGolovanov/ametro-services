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
    raise FileNotFoundError('File with extension %s not found into %s' % (file_ext, path))


def find_files_by_extension(path, file_ext):
    file_ext = file_ext.lower()
    file_list = []
    for file_name in os.listdir(path):
        if file_name.lower().endswith(file_ext):
            file_list.append(os.path.join(path, file_name))
    return file_list


def read_all_lines(source_file_path):
    source_formats = ['windows-1251', 'iso-8859-1', 'ascii']
    for source_format in source_formats:
        try:
            lines = []
            with codecs.open(source_file_path, 'rU', source_format) as source_file:
                for line in source_file:
                    lines.append(line)
            return lines
        except UnicodeDecodeError:
            pass

    raise IOError("Error: failed to read all lines from '" + source_file_path + "'.")


def get_file_name(path):
    head, tail = os.path.split(path)
    return tail


def get_file_name_without_ext(path):
    file_name = get_file_name(path)
    if '.' not in file_name:
        return file_name
    last_dot_index = file_name.rindex('.')
    return file_name[:last_dot_index]


def get_file_ext(path):
    file_name = get_file_name(path)
    if '.' not in file_name:
        return None
    last_dot_index = file_name.rindex('.')
    return file_name[last_dot_index+1:]


def find_appropriate_file(path):
    if os.path.isfile(path):
        return path

    lowered_path = path.lower()
    root_path = os.path.dirname(path)

    for file in os.listdir(root_path):
        existing_file = os.path.join(root_path, file)
        if existing_file.lower() == lowered_path:
            return existing_file

    return path
