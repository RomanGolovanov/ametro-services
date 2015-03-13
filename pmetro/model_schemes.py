import os

from pmetro.files import find_files_by_extension, get_file_name_without_ext, find_appropriate_file
from pmetro.graphics import cubic_interpolate
from pmetro.helpers import as_list, as_points, as_int_point_list, as_int_rect_list, as_quoted_list, as_int_rect, \
    round_points_array
from pmetro.log import ConsoleLog
from pmetro.model_objects import MapScheme, MapSchemeLine, MapSchemeStation
from pmetro.ini_files import deserialize_ini, get_ini_attr, get_ini_attr_float, get_ini_attr_bool, get_ini_section, \
    get_ini_attr_int


LOG = ConsoleLog()

__DEFAULT_LINES_WIDTH = 9
__DEFAULT_STATIONS_DIAMETER = 11

__DEFAULT_COLOR = '000000'
__DEFAULT_LABEL_COLOR = '000000'
__DEFAULT_LABEL_BG_COLOR = ''

__SCHEME_GAP_SIZE = 100

__ZERO_COORD = (0, 0)
__NONE_COORD = (None, None)
__ZERO_RECT = (0, 0, 0, 0)
__NONE_RECT = (None, None, None, None)


def load_schemes(map_container, src_path, global_names):
    scheme_files = find_files_by_extension(src_path, '.map')
    if not any(scheme_files):
        raise FileNotFoundError('Cannot found .map files in %s' % src_path)

    default_file = os.path.join(src_path, 'Metro.map')
    if default_file not in scheme_files:
        raise FileNotFoundError('Cannot found Metro.map file in %s' % src_path)

    line_index = __create_line_index(map_container)

    line_colors = dict()

    map_container.schemes = []
    map_container.schemes.append(__load_map(src_path, default_file, line_index, global_names, line_colors))
    for scheme_file_path in [x for x in scheme_files if x != default_file]:
        map_container.schemes.append(__load_map(src_path, scheme_file_path, line_index, global_names, line_colors))


def __load_map(src_path, scheme_file_path, line_index, global_names, line_colors):
    ini = deserialize_ini(scheme_file_path)
    scheme = MapScheme()
    scheme.name = get_file_name_without_ext(scheme_file_path).lower()

    scheme.images = []
    for image_file in as_quoted_list(get_ini_attr(ini, 'Options', 'ImageFileName', '')):
        image_file = image_file.strip()
        image_file_path = find_appropriate_file(os.path.join(src_path, image_file))
        if os.path.isfile(image_file_path):
            scheme.images.append(image_file)
        else:
            LOG.error('Not found file [%s] references in [%s], ignored' % (image_file_path, scheme_file_path))

    scheme_line_width = get_ini_attr_int(ini, 'Options', 'LinesWidth', __DEFAULT_LINES_WIDTH)

    scheme.stations_diameter = get_ini_attr_float(ini, 'Options', 'StationDiameter', __DEFAULT_STATIONS_DIAMETER)
    scheme.lines_width = scheme_line_width
    scheme.upper_case = get_ini_attr_bool(ini, 'Options', 'UpperCase', True)
    scheme.word_wrap = get_ini_attr_bool(ini, 'Options', 'WordWrap', True)

    transports = as_list(get_ini_attr(ini, 'Options', 'Transports', ''))
    if not any(transports):
        transports = ['Metro']
    scheme.transports = [get_file_name_without_ext(x).lower() for x in transports]

    default_transports = as_list(get_ini_attr(ini, 'Options', 'CheckedTransports', ''))
    if not any(default_transports):
        default_transports = ['Metro']
    scheme.default_transports = [get_file_name_without_ext(x).lower() for x in default_transports]

    additional_nodes = __load_additional_nodes(ini)

    scheme.lines = []
    for name in ini:
        if name not in line_index:
            continue

        scheme.lines.append(
            __load_scheme_line(
                name, ini, line_index, scheme_line_width, additional_nodes, global_names[name], line_colors))

    scheme.width, scheme.height = __calculate_scheme_size(scheme)

    return scheme


def __load_scheme_line(name, ini, line_index, scheme_line_width, additional_nodes, line_names, line_colors):
    line = MapSchemeLine()
    line.name = name
    line.display_name = line_names['display_name']

    line.line_color = get_ini_attr(ini, name, 'Color', __get_line_color(name, line_colors))
    line_colors[name] = line.line_color

    line.line_width = get_ini_attr_int(ini, name, 'Width', scheme_line_width)
    line.labels_color = get_ini_attr(ini, name, 'LabelsColor', __DEFAULT_LABEL_COLOR)
    line.labels_bg_color = get_ini_attr(ini, name, 'LabelsBColor', __DEFAULT_LABEL_BG_COLOR)
    line.rect = as_int_rect(get_ini_attr(ini, name, 'Rect', None))

    line.stations, line.segments = __load_scheme_stations_and_segments(
        as_int_point_list(get_ini_attr(ini, name, 'Coordinates', '')),
        as_int_rect_list(get_ini_attr(ini, name, 'Rects', '')),
        line_index[name],
        additional_nodes,
        line_names['stations'])



    return line


def __load_scheme_stations_and_segments(coordinates, rectangles, trp_line, additional_nodes, station_names):
    stations = __load_stations(coordinates, rectangles, station_names, trp_line)

    segments = dict()
    removed_segments = []
    for i in range(len(trp_line.segments)):
        from_id, to_id, delay = trp_line.segments[i]
        min_id, max_id = min(from_id, to_id), max(from_id, to_id)
        segment_id = (min_id, max_id)

        if segment_id in removed_segments:
            continue

        station_start = stations[from_id]
        station_end = stations[to_id]

        if station_start.coord is None or station_end.coord is None:
            continue

        if delay is not None and delay > 0:
            is_working = True
        else:
            is_working = False

        additional_points, is_spline = __get_additional_nodes(
            additional_nodes,
            trp_line.name,
            trp_line.stations[from_id],
            trp_line.stations[to_id])

        if len(additional_points) == 1 and additional_points[0] == __ZERO_COORD:
            removed_segments.append(segment_id)
            # do not show segment with (0,0) in additional nodes
            if segment_id in segments:
                # remove opposite one if exists
                del segments[segment_id]
            continue

        points = list((station_start.coord,)) + additional_points + list((station_end.coord,))
        if is_spline:
            points = round_points_array(cubic_interpolate(points))

        if segment_id in segments:
            added_min_id, added_max_id, added_points, added_is_working = segments[segment_id]
            if len(added_points) > len(points):
                points = added_points
            if added_is_working:
                is_working = True

        segments[segment_id] = (min_id, max_id, points, is_working)

    return [x for x in stations if x.coord is not None], list(sorted(segments.values()))


def __load_stations(coordinates, rectangles, station_names, trp_line):
    stations = []
    for i in range(len(trp_line.stations)):
        name = trp_line.stations[i]

        station = MapSchemeStation()
        station.name = name
        station.display_name = station_names[name]

        if i < len(coordinates) and coordinates[i] is not None \
                and coordinates[i] != __ZERO_COORD and coordinates[i] != __NONE_COORD:
            station.coord = coordinates[i]
        else:
            station.coord = None

        if i < len(rectangles) and rectangles[i] is not None \
                and rectangles[i] != __ZERO_RECT and rectangles[i] != __NONE_RECT:
            station.rect = rectangles[i]
        else:
            station.rect = None

        station.is_working = __is_station_working(i, trp_line.segments)

        stations.append(station)
    return stations


def __get_additional_nodes(nodes, line, station_from, station_to):
    key = '%s,%s,%s' % (line, station_from, station_to)
    if key not in nodes:
        return list(), False
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
        is_spline = parts[-1].strip() == 'spline'
        points = as_points(parts[3:])

        key = '%s,%s,%s' % (line, station_from, station_to)
        obj[key] = (points, is_spline)
    return obj


def __calculate_scheme_size(scheme):
    width = 0
    height = 0
    for line in scheme.lines:
        for station in line.stations:
            if station.coord is None:
                continue
            (x, y) = station.coord
            width = max(width, int(x))
            height = max(height, int(y))

        for (from_id, to_id, points, is_working) in line.segments:
            if points is None or not any(points):
                continue
            for (x, y) in points:
                width = max(width, int(x))
                height = max(height, int(y))
    return width + __SCHEME_GAP_SIZE, height + __SCHEME_GAP_SIZE


def __create_line_index(map_container):
    by_line_index = {}
    for trp in map_container.transports:
        for line in trp.lines:
            by_line_index[line.name] = line
    return by_line_index


def __get_display_name(name, aliases):
    if name in aliases:
        return aliases[name]
    return name


def __get_line_color(name, line_colors):
    if name in line_colors:
        return line_colors[name]
    return __DEFAULT_COLOR


def __is_station_working(station_id, segments):
    for from_id, to_id, delay in segments:
        if station_id in (from_id, to_id) and delay is not None and delay > 0:
            return True
    return False


