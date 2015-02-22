import os

from pmetro.files import find_files_by_extension, get_file_name_without_ext
from pmetro.helpers import as_list
from pmetro.model_helpers import DelaysString, StationsString
from pmetro.readers import deserialize_ini, get_ini_attr, get_ini_section, get_ini_sections


class MapSegment(object):
    def __init__(self, from_station, to_station, delay):
        self.from_station = from_station
        self.to_station = to_station
        self.delay = delay


class MapTransfer(object):
    def __init__(self):
        self.name = ''
        self.from_line = ''
        self.from_station = ''
        self.to_line = ''
        self.to_station = ''
        self.delay = None
        self.state = None


class MapLine(object):
    def __init__(self):
        self.name = ''
        self.map = ''

        self.id = ''
        self.stations = []
        self.segments = []


class MapTransport(object):
    def __init__(self):
        self.name = ''
        self.type = ''
        self.lines = []
        self.transfers = []


class MapContainer(object):
    def __init__(self):
        self.name = ''
        self.comment = ''
        self.description = ''
        self.city = ''
        self.country = ''

        self.delays = []
        self.transports = []
        self.stations = []
        self.images = []
        self.maps = []
        self.texts = []


def load_map(path, map_info=None):
    map_container = create_metadata(path)
    load_transports(map_container, path)

    return map_container


def split_by_commas(text):
    return [x.strip() for x in str(text).split(',')]


def create_metadata(path):
    metadata_files = find_files_by_extension(path, '.cty')

    if not any(metadata_files):
        raise FileNotFoundError('Cannot found .cty file in %s' % path)

    metadata = deserialize_ini(sorted(metadata_files)[0])

    map_container = MapContainer()
    map_container.delays = split_by_commas(get_ini_attr(metadata, 'Options', 'DelayNames', 'Day,Night'))

    return map_container


def load_transports(map_container, path):
    transport_files = find_files_by_extension(path, '.trp')
    if not any(transport_files):
        raise FileNotFoundError('Cannot found .cty file in %s' % path)

    default_file = os.path.join(path, 'Metro.trp')

    if default_file not in transport_files:
        raise FileNotFoundError('Cannot found Metro.trp file in %s' % path)

    map_container.transports.append(load_transport(default_file))
    for trp in [x for x in transport_files if x != default_file]:
        map_container.transports.append(load_transport(trp))


def load_transport(path):
    ini = deserialize_ini(path)
    transport = MapTransport()
    transport.name = get_file_name_without_ext(path)
    transport.type = get_ini_attr(ini, 'Options', 'Type', 'Метро')

    transport.lines = load_lines(ini)
    transport.transfers = load_transfers(ini)

    return transport


def load_transfers(ini):
    section = get_ini_section(ini, 'Transfers')
    if section is None:
        return []

    transfers = []
    for name in section:
        transfer = MapTransfer()
        transfer.name = name
        params = as_list(section[name])
        transfer.from_line, transfer.from_station, transfer.to_line, transfer.to_station = params[:4]
        transfer.delay = float(params[4])
        if len(params) > 5:
            transfer.state = params[5]
        transfers.append(transfer)
    return transfers


def load_lines(ini):
    sections = get_ini_sections(ini, 'Line')
    if not any(sections):
        return []

    lines = []
    for section_name in sections:
        line = MapLine()
        line.name = get_ini_attr(ini, section_name, 'Name')
        line.id = get_ini_attr(ini, section_name, 'Alias', line.name)
        line.map = get_ini_attr(ini, section_name, 'LineMap')
        line.stations, line.segments = load_line_segments(
            get_ini_attr(ini, section_name, 'Stations'),
            get_ini_attr(ini, section_name, 'Driving'),
            get_ini_attr(ini, section_name, 'Aliases'))

        line.delays = as_list(get_ini_attr(ini, section_name, 'Delays', ''))
        lines.append(line)
    return lines


def load_line_segments(stations_text, drivings_text, aliases_text):
    stations_iter = StationsString(stations_text)
    delays_iter = DelaysString(drivings_text)

    stations = []
    segments = []

    to_station = ''
    to_delay = 0

    from_station = None
    from_delay = None

    this_station = stations_iter.next()

    while True:
        if stations_iter.next_separator == '(':
            idx = 0
            delays = delays_iter.next_block()
            while stations_iter.has_next() and stations_iter.next_separator != ')':
                is_forward = True

                bracketed_station_name = stations_iter.next()
                if bracketed_station_name.startswith('-'):
                    bracketed_station_name = bracketed_station_name[1:]
                    is_forward = not is_forward

                if bracketed_station_name is not None and len(bracketed_station_name) > 0:
                    if idx < len(delays):
                        delay = delays[idx]
                    else:
                        delay = None

                    if is_forward:
                        segments.append(MapSegment(this_station, bracketed_station_name, delay))
                    else:
                        segments.append(MapSegment(bracketed_station_name, this_station, delay))
                idx += 1
            # /while
            from_station = this_station
            from_delay = None
            to_delay = None
            if not stations_iter.has_next():
                break

            this_station = stations_iter.next()
            stations.append(this_station)

        else:

            to_station = stations_iter.next()
            stations.append(to_station)

            if delays_iter.begin_bracket():
                delays = delays_iter.next_bracket()
                to_delay = delays[0]
                from_delay = delays[1]
            else:
                to_delay = delays_iter.next()

            this_from_segment = MapSegment(this_station, from_station, from_delay)
            this_to_segment = MapSegment(this_station, to_station, to_delay)

            if from_station is not None and not (this_from_segment in segments):
                if from_delay is None:
                    opposite_segment = MapSegment(from_station, this_station, None)
                    for si in segments:
                        if opposite_segment == si:
                            this_from_segment.delay = si.delay
                segments.append(this_from_segment)
            if to_station is not None and not (this_to_segment in segments):
                segments.append(this_to_segment)

            from_station = this_station

            from_delay = to_delay
            to_delay = None

            this_station = to_station
            to_station = None

            if not (stations_iter.has_next()):
                this_from_segment = MapSegment(this_station, from_station, from_delay)
                if from_station is not None and not (this_from_segment in segments):
                    if from_delay is None:
                        opposite_segment = MapSegment(from_station, this_station, None)
                        for si in segments:
                            if opposite_segment == si:
                                this_from_segment.delay = si.delay
                    segments.append(this_from_segment)

        if not (stations_iter.has_next()):
            break

    return stations, segments


