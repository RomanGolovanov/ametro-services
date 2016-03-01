import os
import shutil

from PIL import Image

from pmetro import log
from pmetro.graphics import cubic_interpolate
from pmetro.helpers import un_bugger_for_float, default_if_empty, as_points, round_points_array, \
    as_int_point_list, as_int_rect_list, as_nullable_list, as_delay, as_nullable_list_stripped
from pmetro.ini_files import get_ini_attr_int, get_ini_attr_float, get_ini_attr_bool, get_ini_composite_attr
from pmetro.pmz_meta import load_metadata
from pmetro.entities import MapScheme, MapSchemeLine, MapSchemeStation
from pmetro.pmz_static import load_static
from pmetro.pmz_schemes import create_line_index, create_scheme_index, create_transport_index, \
    suggest_scheme_display_name_and_type, create_visible_transfer_list
from pmetro.pmz_transports import get_transport_type, StationsString, parse_station_and_delays
from pmetro.file_utils import find_files_by_extension, find_file_by_extension
from pmetro.helpers import as_dict, as_quoted_list
from pmetro.ini_files import deserialize_ini, get_ini_attr, get_ini_attr_collection, get_ini_sections, get_ini_section
from pmetro.pmz_texts import StationIndex, TextIndexTable, load_texts, TEXT_AS_COMMON_LANGUAGE
from pmetro.entities import MapMetadata, MapContainer, MapTransport, MapTransportLine
from pmetro.pmz_transports import parse_line_delays
from pmetro.file_utils import get_file_ext, get_file_name_without_ext, find_appropriate_file
from pmetro.serialization import store_model
from pmetro.vec2svg import convert_vec_to_svg


def convert_map(city_id, file_name, timestamp, src_path, dst_path, logger, geoname_provider):
    logger.message("Begin processing %s" % src_path)
    importer = PmzImporter(logger, geoname_provider)
    container = importer.import_pmz(src_path, city_id, file_name, timestamp)
    __convert_resources(container, src_path, dst_path, logger)
    store_model(container, dst_path)


def __convert_resources(map_container, src_path, dst_path, logger):
    res_path = os.path.join(dst_path, 'res')
    if not os.path.isdir(res_path):
        os.mkdir(res_path)

    schemes_path = os.path.join(res_path, 'schemes')
    if not os.path.isdir(schemes_path):
        os.mkdir(schemes_path)
    for scheme in map_container.schemes:
        converted_images = []
        for scheme_image in scheme.images:
            if scheme_image is None:
                continue

            converted_file_path = __convert_static_file(src_path, scheme_image, schemes_path, logger)
            if converted_file_path is None:
                continue

            converted_images.append(os.path.relpath(converted_file_path, dst_path).replace('\\', '/'))

        scheme.images = converted_images

    images_path = os.path.join(res_path, 'stations')
    if not os.path.isdir(images_path):
        os.mkdir(images_path)

    converted_images = []
    for image in map_container.images:

        if image.image is None:
            continue

        converted_file_path = __convert_static_file(src_path, image.image, images_path, logger)
        if converted_file_path is None:
            continue

        image.image = os.path.relpath(converted_file_path, dst_path).replace('\\', '/')
        converted_images.append(image)

    map_container.images = converted_images


def __convert_static_file(src_path, src_name, dst_path, logger):
    __FILE_CONVERTERS = {
        'vec': (convert_vec_to_svg, 'svg'),
        'bmp': (lambda src, dst, l: Image.open(src).save(dst), 'png'),
        'gif': (lambda src, dst, l: Image.open(src).save(dst), 'png'),
        'png': (lambda src, dst, l: shutil.copy(src, dst), 'png')
    }

    src_file_path = find_appropriate_file(os.path.join(src_path, src_name))

    if not os.path.isfile(src_file_path):
        logger.error('Not found image file %s' % src_file_path)
        return None

    src_file_ext = get_file_ext(src_file_path)
    if src_file_ext in __FILE_CONVERTERS:
        new_ext = __FILE_CONVERTERS[src_file_ext][1]
        dst_file_path = os.path.join(dst_path, get_file_name_without_ext(src_name.lower()) + '.' + new_ext)
        logger.debug('Convert %s' % src_file_path)
        __FILE_CONVERTERS[src_file_ext][0](src_file_path, dst_file_path, logger)
    else:
        logger.warning('No converters found for file %s, copy file' % src_file_path)
        dst_file_path = os.path.join(dst_path, src_name.lower())
        shutil.copy(src_file_path, dst_file_path)

    return dst_file_path


class PmzImporter(object):
    def __init__(self, logger, geoname_provider):
        self.__logger = logger
        self.__geoname_provider = geoname_provider

    def import_pmz(self, path, city_id, file_name, timestamp):

        station_index = StationIndex()
        text_index_table = TextIndexTable()

        transport_importer = PmzTransportImporter(
            path,
            file_name,
            station_index,
            text_index_table
        )
        imported_transports = transport_importer.import_transports()

        try:
            station_index.ensure_no_pending_stations()
        except ValueError as e:
            self.__logger.warning(e)

        scheme_importer = PmzSchemeImporter(
            path,
            station_index,
            text_index_table,
            imported_transports,
            self.__logger
        )

        imported_schemes = scheme_importer.import_schemes()

        city_info = self.__geoname_provider.get_city_info(city_id)

        container = MapContainer()
        container.meta = MapMetadata(city_id,
                                     file_name,
                                     timestamp,
                                     city_info.latitude,
                                     city_info.longitude,
                                     text_index_table.as_text_id(self.__extract_map_description(path),
                                                                 text_type=TEXT_AS_COMMON_LANGUAGE),
                                     text_index_table.as_text_id('Imported from http://pmetro.su',
                                                                 text_type=TEXT_AS_COMMON_LANGUAGE))
        container.transports = imported_transports
        container.schemes = imported_schemes

        load_static(container, path)
        load_metadata(container, path, text_index_table)
        load_texts(container, text_index_table)

        valid = self.__validate(container)

        self.__logger.info(
            "Map loaded, text compression: {0}, text size: {1}, valid: {2}".format(
                text_index_table.get_compression(),
                text_index_table.get_text_length(),
                valid))
        return container

    @staticmethod
    def __extract_map_description(map_path):
        ini = deserialize_ini(find_file_by_extension(map_path, '.cty'))
        comments = get_ini_composite_attr(ini, 'Options', 'Comment')
        authors = get_ini_composite_attr(ini, 'Options', 'MapAuthors')

        lines = []
        if comments is not None:
            lines.append(comments)
        if authors is not None:
            lines.append(authors)

        if not lines:
            return None
        return '\n'.join(lines)

    def __validate(self, container):

        valid = True

        delays_count = len(container.meta.delays)
        for transport in container.transports:
            for line in transport.lines:
                if not line.delays or len(line.delays) == delays_count:
                    continue

                valid = False

                if len(line.delays) < delays_count:
                    line.delays.extend([0 for _ in range(delays_count - len(line.delays))])
                    continue

                self.__logger.error(
                    "Delays in line \'{0}\' ({1}) or {2}.trp is not valid for map delay list {3}".format(
                        line.name,
                        line.delays,
                        transport.name,
                        container.meta.delays))

        return valid


class PmzTransportImporter(object):
    def __init__(self, path, map_file_name, station_index, text_index_table):
        if not station_index:
            station_index = StationIndex()
        if not text_index_table:
            text_index_table = TextIndexTable()

        self.__path = path
        self.__map_file_name = map_file_name
        self.__station_index = station_index
        self.__text_index_table = text_index_table

    def import_transports(self):
        files = sorted(find_files_by_extension(self.__path, '.trp'))
        if not any(files):
            raise FileNotFoundError('Cannot found .trp files in %s' % self.__path)

        default_file = os.path.join(self.__path, 'Metro.trp')
        if default_file not in files:
            raise FileNotFoundError('Cannot found Metro.trp file in %s' % self.__path)

        return [self.__import_transport(default_file)] + \
               [self.__import_transport(x) for x in files if x != default_file]

    def __import_transport(self, file):
        ini = deserialize_ini(file)
        name = get_file_name_without_ext(file).lower()
        return MapTransport(
            name,
            get_transport_type(self.__map_file_name, name, ini),
            self.__import_lines(ini),
            self.__import_transfers(ini)
        )

    def __import_lines(self, ini):
        sections = get_ini_sections(ini, 'Line')
        if not any(sections):
            return []

        lines = []
        for section_name in sorted(sections):
            line_name = get_ini_attr(ini, section_name, 'Name')
            line_display_name = get_ini_attr(ini, section_name, 'Alias', line_name)
            line_map = get_ini_attr(ini, section_name, 'LineMap')
            stations_text = get_ini_attr(ini, section_name, 'Stations')
            drivings_text = get_ini_attr(ini, section_name, 'Driving')
            aliases_text = get_ini_attr(ini, section_name, 'Aliases')
            line_delays = get_ini_attr_collection(ini, section_name, 'Delay')

            stations = self.__get_stations(line_name, stations_text, as_dict(aliases_text))
            segments = self.__get_segments(stations, stations_text, drivings_text)

            lines.append(MapTransportLine(
                line_name,
                self.__text_index_table.as_text_id(line_display_name),
                get_file_name_without_ext(line_map).lower() if line_map is not None else None,
                stations,
                segments,
                parse_line_delays(line_name, line_delays)
            ))

        return lines

    def __import_transfers(self, ini):
        section = get_ini_section(ini, 'Transfers')
        if section is None:
            return []
        return list(self.__parse_transfers(section))

    def __parse_transfers(self, section):
        for name in sorted(section):
            if str(name).startswith('__'):
                continue
            params = as_quoted_list(section[name])
            from_uid = self.__station_index.get_station_id(params[0], params[1])
            to_uid = self.__station_index.get_station_id(params[2], params[3])

            if len(params) > 4:
                # TODO: FIX SOURCE!
                delay = as_delay(un_bugger_for_float(params[4]))
            else:
                delay = None

            if len(params) > 5:
                flag = params[5].strip() != 'invisible'
            else:
                flag = True
            yield from_uid, to_uid, delay, flag

    def __get_stations(self, line_name, stations_text, station_aliases):
        stations = []
        stations_iter = StationsString(stations_text)
        quoted = False
        while stations_iter.has_next():

            if stations_iter.next_separator == '(':
                quoted = True

            if stations_iter.next_separator == ')':
                quoted = False

            name, display_name = stations_iter.next()

            if not quoted:

                station_uid = self.__station_index.register_station(line_name, name)

                if display_name in station_aliases:
                    display_name = station_aliases[display_name]

                stations.append((station_uid, name, self.__text_index_table.as_text_id(display_name)))

        return stations

    @staticmethod
    def __get_segments(stations, stations_text, drivings_text):
        segments = []
        __, raw_segments = parse_station_and_delays(stations_text, drivings_text)
        for station_from, station_to, delay in raw_segments:
            segments.append((stations[station_from][0], stations[station_to][0], delay))

        return segments


def get_scheme_size(scheme, gap_size):
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
    return width + gap_size, height + gap_size


class PmzSchemeImporter(object):
    default_lines_width = 9
    default_diameter = 11
    default_color = '000000'
    default_labels_color = '000000'
    default_labels_background_color = '-1'
    default_scheme_gap_size = 150

    empty_coord = [(None, None), (0, 0), (-1, -1), (-2, -2)]
    empty_rect = [(None, None, None, None), (0, 0, 0, 0)]

    def __init__(self, path, station_index, text_index_table, transports, logger=None):
        if not station_index:
            station_index = StationIndex()
        if not text_index_table:
            text_index_table = TextIndexTable()
        if not logger:
            logger = log.ConsoleLog()

        self.__path = path
        self.__station_index = station_index
        self.__text_index_table = text_index_table

        self.logger = logger

        self.__line_index = create_line_index(transports)
        self.__scheme_index = create_scheme_index(transports)
        self.__transport_index = create_transport_index(transports)
        self.__transfers_list = create_visible_transfer_list(transports)
        self.__line_colors = dict()
        self.__global_names = {}

    def import_schemes(self):
        files = sorted(find_files_by_extension(self.__path, '.map'))
        if not any(files):
            raise FileNotFoundError('Cannot found .map files in %s' % self.__path)

        default_file = os.path.join(self.__path, 'Metro.map')
        if default_file not in files:
            raise FileNotFoundError('Cannot found Metro.map file in %s' % self.__path)

        return [self.__import_scheme(default_file)] + \
               [self.__import_scheme(x) for x in files if x != default_file]

    def __import_scheme(self, file):
        ini = deserialize_ini(file)
        name = get_file_name_without_ext(file).lower()
        map_files = get_ini_attr(ini, 'Options', 'ImageFileName', '')
        line_width = get_ini_attr_int(ini, 'Options', 'LinesWidth', PmzSchemeImporter.default_lines_width)
        diameter = get_ini_attr_float(ini, 'Options', 'StationDiameter', PmzSchemeImporter.default_diameter)
        is_upper_case = get_ini_attr_bool(ini, 'Options', 'UpperCase', True)
        is_word_wrap = get_ini_attr_bool(ini, 'Options', 'WordWrap', True)
        is_vector = get_ini_attr(ini, 'Options', 'IsVector', '1') == '1'
        additional_node_section = get_ini_section(ini, 'AdditionalNodes')

        transports = default_if_empty(
            as_nullable_list_stripped(get_ini_attr(ini, 'Options', 'Transports')), ['Metro'])

        default_transports = default_if_empty(
            as_nullable_list_stripped(get_ini_attr(ini, 'Options', 'CheckedTransports', None)), ['Metro'])

        display_name, type_name = \
            suggest_scheme_display_name_and_type(
                name,
                self.__transport_index,
                self.__scheme_index,
                self.__text_index_table)

        scheme = MapScheme()
        scheme.name = name

        scheme.name_text_id = self.__text_index_table.as_text_id(display_name)
        scheme.type_text_id = self.__text_index_table.as_text_id(type_name, TEXT_AS_COMMON_LANGUAGE)
        scheme.type_name = type_name

        scheme.images = self.__get_images_links(file, as_quoted_list(map_files))
        scheme.lines_width = line_width
        scheme.stations_diameter = diameter
        scheme.upper_case = is_upper_case
        scheme.word_wrap = is_word_wrap
        scheme.is_vector = is_vector
        scheme.transports = [get_file_name_without_ext(x).lower() for x in transports]
        scheme.default_transports = [get_file_name_without_ext(x).lower() for x in default_transports]
        additional_nodes = self.__load_additional_nodes(file, additional_node_section)

        scheme.lines = []
        for name in ini:
            if name not in self.__line_index:
                continue

            scheme.lines.append(self.__load_scheme_line(ini, name, line_width, additional_nodes))

        scheme.transfers = self.__create_scheme_transfers(scheme.lines)
        scheme.width, scheme.height = get_scheme_size(scheme, PmzSchemeImporter.default_scheme_gap_size)

        return scheme

    def __get_images_links(self, parent_file, relative_links):
        images = []
        root_dir = os.path.dirname(parent_file)
        for link in [find_appropriate_file(os.path.join(root_dir, link)) for link in relative_links]:
            if os.path.isfile(link):

                images.append(os.path.relpath(link, root_dir))
            else:
                self.logger.error('Not found file %s references in %s, ignored' % (link, parent_file))
        return images

    def __load_additional_nodes(self, file, ini_section):
        if not ini_section:
            return dict(), False

        nodes = dict()
        for name in ini_section:
            text = ini_section[name]
            if not text:
                continue

            parts = as_quoted_list(text)
            if len(parts) < 5:
                self.logger.warning('Skipped invalid additional node \'{0}\' in {1}: \'{2}\''.format(name, file, text))
                continue

            line, station_from, station_to = parts[:3]
            points = as_points(parts[3:])
            is_spline = parts[-1] == 'spline'

            from_uid = self.__station_index.get_station_id(line, station_from)
            to_uid = self.__station_index.get_station_id(line, station_to)

            nodes[(from_uid, to_uid)] = points, is_spline
        return nodes

    def __load_scheme_line(self, ini, line_name, scheme_line_width, additional_nodes):

        text_id = self.__line_index[line_name].text_id
        line_color = self.__get_line_color(line_name, get_ini_attr(ini, line_name, 'Color'))
        line_width = get_ini_attr_int(ini, line_name, 'Width', scheme_line_width)
        labels_color = get_ini_attr(ini, line_name, 'LabelsColor', PmzSchemeImporter.default_labels_color)
        labels_bg_color = get_ini_attr(ini, line_name, 'LabelsBColor',
                                       PmzSchemeImporter.default_labels_background_color)

        stations, segments = self.__load_stations_and_segments(
            line_name,
            as_int_point_list(get_ini_attr(ini, line_name, 'Coordinates', '')),
            as_int_rect_list(get_ini_attr(ini, line_name, 'Rects', '')),
            additional_nodes)

        return MapSchemeLine(
            line_name,
            text_id,
            line_color,
            line_width,
            labels_color,
            labels_bg_color,
            stations,
            segments
        )

    def __get_line_color(self, name, proposed_color):
        if proposed_color:
            self.__line_colors[name] = proposed_color
            return proposed_color

        if name in self.__line_colors:
            return self.__line_colors[name]

        return PmzSchemeImporter.default_color

    def __load_stations_and_segments(self, line_name, coord_list, rect_list, additional_nodes):
        stations = self.__load_stations(line_name, coord_list, rect_list)
        station_index = dict([(s.uid, s) for s in stations])

        segments = dict()
        removed_segments = []
        for from_id, to_id, delay in self.__line_index[line_name].segments:

            min_id, max_id = min(from_id, to_id), max(from_id, to_id)
            segment_id = (min_id, max_id)

            if segment_id in removed_segments:
                continue

            start_coord = station_index[from_id].coord
            end_coord = station_index[to_id].coord

            if start_coord is None or end_coord is None:
                continue

            if delay is not None and delay > 0:
                is_working = True
            else:
                is_working = False

            is_spline = False
            pts = list()
            if (from_id, to_id) in additional_nodes:
                pts, is_spline = additional_nodes[(from_id, to_id)]
            else:
                if (to_id, from_id) in additional_nodes:
                    pts, is_spline = additional_nodes[(to_id, from_id)]
                    if pts:
                        pts = list(reversed(pts))

            if len(pts) == 1 and pts[0] in PmzSchemeImporter.empty_coord:
                removed_segments.append(segment_id)
                # do not show segment with (0,0) in additional nodes
                if segment_id in segments:
                    # remove opposite one if exists
                    del segments[segment_id]
                continue

            points = list((start_coord,)) + pts + list((end_coord,))
            if is_spline:
                points = round_points_array(cubic_interpolate(points))

            if segment_id in segments:
                added_min_id, added_max_id, added_points, added_is_working = segments[segment_id]
                if len(added_points) > len(points):
                    points = added_points
                if added_is_working:
                    is_working = True

            segments[segment_id] = (min_id, max_id, points, is_working)

        return stations, list(sorted(segments.values()))

    def __load_stations(self, line_name, coord_list, rect_list):
        trp_line = self.__line_index[line_name]

        stations = []
        for i, (uid, name, text_id) in enumerate(trp_line.stations):

            station = MapSchemeStation()
            station.uid = uid
            station.name = name
            station.text_id = text_id

            if i < len(coord_list) and coord_list[i] is not None and coord_list[i] not in PmzSchemeImporter.empty_coord:
                station.coord = coord_list[i]
            else:
                station.coord = None

            if i < len(rect_list) and rect_list[i] is not None and rect_list[i] not in PmzSchemeImporter.empty_rect:
                station.rect = rect_list[i]
            else:
                station.rect = None

            station.is_working = self.__is_station_working(uid, trp_line.segments)

            stations.append(station)
        return stations

    def __create_scheme_transfers(self, lines):
        scheme_stations = dict()
        for line in lines:
            for station in line.stations:
                scheme_stations[station.uid] = station

        transfers = []
        for from_uid, to_uid in self.__transfers_list:

            if from_uid not in scheme_stations or to_uid not in scheme_stations:
                continue

            from_station = scheme_stations[from_uid]
            to_station = scheme_stations[to_uid]

            transfers.append((
                from_uid,
                to_uid,
                from_station.coord,
                to_station.coord
            ))

        return transfers

    @staticmethod
    def __is_station_working(uid, segments):
        for from_id, to_id, delay in segments:
            if uid in (from_id, to_id) and delay is not None and delay > 0:
                return True
        return False
