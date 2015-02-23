import os

from pmetro.files import find_files_by_extension, get_file_name_without_ext
from pmetro.graphics import cubic_interpolate
from pmetro.helpers import as_list, as_points, as_int_point_list, as_int_rect_list, as_quoted_list
from pmetro.log import ConsoleLog
from pmetro.model_objects import MapScheme, MapSchemeLine, MapSchemeStation
from pmetro.ini_files import deserialize_ini, get_ini_attr, get_ini_attr_float, get_ini_attr_bool, get_ini_section


LOG = ConsoleLog()

__DEFAULT_LINES_WIDTH = 9

__DEFAULT_STATIONS_DIAMETER = 11

__DEFAULT_COLOR = '000000'
__DEFAULT_LABEL_COLOR = '000000'
__DEFAULT_LABEL_BG_COLOR = 'FFFFFFFF'


def load_schemes(map_container, src_path):
    scheme_files = find_files_by_extension(src_path, '.map')
    if not any(scheme_files):
        raise FileNotFoundError('Cannot found .map files in %s' % src_path)

    default_file = os.path.join(src_path, 'Metro.map')
    if default_file not in scheme_files:
        raise FileNotFoundError('Cannot found Metro.map file in %s' % src_path)

    line_index = __create_line_index(map_container)

    map_container.schemes = []
    map_container.schemes.append(__load_map(src_path, default_file, line_index))
    for scheme_file_path in [x for x in scheme_files if x != default_file]:
        map_container.schemes.append(__load_map(src_path, scheme_file_path, line_index))


def __load_map(src_path, scheme_file_path, line_index):
    ini = deserialize_ini(scheme_file_path)
    scheme = MapScheme()
    scheme.name = get_file_name_without_ext(scheme_file_path)

    scheme.images = []

    for image_file in as_quoted_list(get_ini_attr(ini, 'Options', 'ImageFileName', '')):
        image_file = image_file.strip()
        image_file_path = os.path.join(src_path, image_file)
        if os.path.isfile(image_file_path):
            scheme.images.append(image_file)
        else:
            LOG.error('Not found file [%s] references in [%s], ignored' % (image_file_path, scheme_file_path))

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

    additional_nodes = __load_additional_nodes(ini)

    scheme.lines = []
    for name in ini:
        if name not in line_index:
            continue
        scheme.lines.append(__load_scheme_line(name, ini, line_index, scheme_line_width, additional_nodes))

    return scheme


def __load_scheme_line(name, ini, line_index, scheme_line_width, additional_nodes):
    line = MapSchemeLine()
    line.name = name

    line.line_color = get_ini_attr(ini, name, 'Color', __DEFAULT_COLOR)
    line.line_width = get_ini_attr(ini, name, 'Width', scheme_line_width)
    line.labels_color = get_ini_attr(ini, name, 'LabelsColor', __DEFAULT_LABEL_COLOR)
    line.labels_bg_color = get_ini_attr(ini, name, 'LabelsBColor', __DEFAULT_LABEL_BG_COLOR)
    line.rect = get_ini_attr(ini, name, 'Rect', None)

    line.stations, line.segments = __load_scheme_stations(
        as_int_point_list(get_ini_attr(ini, name, 'Coordinates', '')),
        as_int_rect_list(get_ini_attr(ini, name, 'Rects', '')),
        line_index[name],
        additional_nodes)

    return line


def __load_scheme_stations(coordinates, rectangles, trp_line, additional_nodes):
    stations = []
    coord_len = len(coordinates)
    rect_len = len(rectangles)
    for i in range(len(trp_line.stations)):
        station = MapSchemeStation()
        station.name = __get_line_name(trp_line.stations[i], trp_line.aliases)
        if i < coord_len and coordinates[i] != (0, 0):
            station.coord = coordinates[i]
        else:
            station.coord = None

        if i < rect_len and rectangles[i] != (0, 0, 0, 0):
            station.rect = rectangles[i]
        else:
            station.rect = None
        stations.append(station)

    segments = dict()
    for i in range(len(trp_line.segments)):
        trp_segment = trp_line.segments[i]
        from_id = trp_segment[0]
        to_id = trp_segment[1]
        from_station = stations[from_id]
        to_station = stations[to_id]

        if from_station.coord == (0, 0) or to_station.coord == (0, 0):
            continue

        nodes = __get_additional_nodes(
            additional_nodes,
            trp_line.name,
            trp_line.stations[from_id],
            trp_line.stations[to_id])

        additional_points, is_spline = (nodes['points'], nodes['is_spline'])

        points = list((from_station.coord,)) + additional_points + list((to_station.coord,))
        if is_spline:
            points = cubic_interpolate(points)

        min_id, max_id = min(from_id, to_id), max(from_id, to_id)

        if (min_id, max_id) in segments:
            added_segment = segments[(min_id, max_id)]
            added_segment_points = added_segment[2]
            if len(added_segment_points) > len(points):
                continue

        segments[(min_id, max_id)] = (min_id, max_id, points)

    return stations, list(sorted(segments.values()))


def __get_additional_nodes(nodes, line, station_from, station_to):
    key = '%s,%s,%s' % (line, station_from, station_to)
    if key not in nodes:
        return dict(points=list(), is_spline=False)
    return nodes[key]


def __load_additional_nodes(ini):
    section = get_ini_section(ini, 'AdditionalNodes')
    if section is None:
        return {}
    obj = {}
    for name in section:
        text = get_ini_attr(ini, 'AdditionalNodes', name, '')
        parts = as_quoted_list(text)
        if len(parts) == 0:
            continue

        if len(parts) < 5:
            LOG.warning('Skipped additional node [%s] in [%s] - insufficient parameters in [%s]' % (
                name, ini['__FILE_NAME__'], text))

        line, station_from, station_to = parts[:3]
        is_spline = parts[-1] == 'spline'
        points = as_points(parts[3:])

        key = '%s,%s,%s' % (line, station_from, station_to)
        obj[key] = dict(points=points, is_spline=is_spline)
    return obj


def __create_line_index(map_container):
    by_line_index = {}
    for trp in map_container.transports:
        for line in trp.lines:
            by_line_index[line.name] = line
    return by_line_index


def __get_line_name(name, aliases):
    if name in aliases:
        return aliases[name]
    return name
