import os

from pmetro.files import find_files_by_extension, get_file_name_without_ext
from pmetro.model_objects import MapTransport, MapScheme
from pmetro.readers import deserialize_ini, get_ini_attr


def load_schemes(map_container, path):
    scheme_files = find_files_by_extension(path, '.map')
    if not any(scheme_files):
        raise FileNotFoundError('Cannot found .map files in %s' % path)

    default_file = os.path.join(path, 'Metro.map')
    if default_file not in scheme_files:
        raise FileNotFoundError('Cannot found Metro.map file in %s' % path)

    map_container.schemes.append(load_map(default_file))

    for m in [x for x in scheme_files if x != default_file]:
        map_container.transports.append(load_map(m))


def load_map(path):
    ini = deserialize_ini(path)
    scheme = MapScheme()
    scheme.name = get_file_name_without_ext(path)


