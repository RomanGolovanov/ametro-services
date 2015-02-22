import os

from pmetro.files import find_files_by_extension, get_file_name_without_ext, get_file_ext
from pmetro.helpers import as_list
from pmetro.log import ConsoleLog
from pmetro.model_objects import MapScheme, MapSchemeLine
from pmetro.readers import deserialize_ini, get_ini_attr, get_ini_attr_float, get_ini_attr_bool


LOG = ConsoleLog()


__EXT_CONVERSION_RULES = {
    'vec': 'svg',
    'gif': 'png',
    'bmp': 'png',
    'png': 'png'
}

__DEFAULT_LINES_WIDTH = 9

__DEFAULT_STATIONS_DIAMETER = 11

__DEFAULT_COLOR = '000000'
__DEFAULT_LABEL_COLOR = '000000'
__DEFAULT_LABEL_BG_COLOR = 'FFFFFFFF'

def load_schemes(map_container, path):
    scheme_files = find_files_by_extension(path, '.map')
    if not any(scheme_files):
        raise FileNotFoundError('Cannot found .map files in %s' % path)

    default_file = os.path.join(path, 'Metro.map')
    if default_file not in scheme_files:
        raise FileNotFoundError('Cannot found Metro.map file in %s' % path)

    line_index = __create_line_index(map_container)

    map_container.schemes.append(__load_map(default_file, line_index))

    for m in [x for x in scheme_files if x != default_file]:
        map_container.schemes.append(__load_map(m, line_index))


def __load_map(path, line_index):
    ini = deserialize_ini(path)
    scheme = MapScheme()
    scheme.name = get_file_name_without_ext(path)

    image_file = get_ini_attr(ini, 'Options', 'ImageFileName', None)
    scheme.image = __convert_static_file_name(image_file)

    scheme.stations_diameter = get_ini_attr_float(ini, 'Options', 'StationDiameter', __DEFAULT_STATIONS_DIAMETER)
    scheme.upper_case = get_ini_attr_bool(ini, 'Options', 'UpperCase', True)
    scheme.word_wrap = get_ini_attr_bool(ini, 'Options', 'WordWrap', True)

    transports = as_list(get_ini_attr(ini, 'Options', 'Transports', ''))
    if not any(transports):
        transports = ['Metro']
    scheme.transports = [get_file_name_without_ext(x) for x in transports]

    default_transports = as_list(get_ini_attr(ini, 'Options', 'CheckedTransports', ''))
    if not any(default_transports):
        default_transports = ['Metro']
    scheme.default_transports = [get_file_name_without_ext(x) for x in default_transports]

    scheme_line_width = get_ini_attr(ini, 'Options', 'LinesWidth', __DEFAULT_LINES_WIDTH)

    scheme.lines = []
    for name in ini:
        if name not in line_index:
            continue
        scheme.lines.append(__load_scheme_line(name, ini, line_index, scheme_line_width))

    return scheme


def __load_scheme_line(name, ini, line_index, scheme_line_width):
    line = MapSchemeLine()
    line.name = name

    line.line_color = get_ini_attr(ini, name, 'Color', __DEFAULT_COLOR)
    line.line_width = get_ini_attr(ini, name, 'Width', scheme_line_width)
    line.labels_color = get_ini_attr(ini, name, 'LabelsColor', __DEFAULT_LABEL_COLOR)
    line.labels_bg_color = get_ini_attr(ini, name, 'LabelsBColor', __DEFAULT_LABEL_BG_COLOR)
    line.rect = get_ini_attr(ini, name, 'Rect', None)

    return line


def __convert_static_file_name(image_file_name):
    if image_file_name is None:
        return None
    return get_file_name_without_ext(image_file_name) + '.' + __EXT_CONVERSION_RULES[get_file_ext(image_file_name)]


def __create_line_index(map_container):
    by_line_index = {}

    for trp in map_container.transports:
        for line in trp.lines:
            by_line_index[line.name] = line.stations

    return by_line_index

