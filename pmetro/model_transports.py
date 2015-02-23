import os

from pmetro.files import find_files_by_extension, get_file_name_without_ext, read_all_lines

from pmetro.helpers import as_delay_list, as_quoted_list, un_bugger_for_float, as_delay, as_dict
from pmetro.log import ConsoleLog
from pmetro.model_objects import MapTransport, MapTransportLine
from pmetro.ini_files import deserialize_ini, get_ini_attr, get_ini_section, get_ini_sections, get_ini_attr_collection


LOG = ConsoleLog()

__TRANSPORT_TYPE_DICT = {}
__TRANSPORT_TYPE_DEFAULT = 'Метро'


def load_transports(map_container, path):
    transport_files = find_files_by_extension(path, '.trp')
    if not any(transport_files):
        raise FileNotFoundError('Cannot found .trp files in %s' % path)

    default_file = os.path.join(path, 'Metro.trp')
    if default_file not in transport_files:
        raise FileNotFoundError('Cannot found Metro.trp file in %s' % path)

    map_container.transports = []
    map_container.transports.append(load_transport(map_container.meta.file, default_file))
    for trp in [x for x in transport_files if x != default_file]:
        map_container.transports.append(load_transport(map_container.meta.map_id, trp))


def load_transport(file_name, path):
    ini = deserialize_ini(path)
    transport = MapTransport()
    transport.name = get_file_name_without_ext(path)
    transport.type = __get_transport_type(file_name, transport.name, ini)
    if transport.type is None:
        transport.type = 'Метро'
        LOG.info('Empty transport type for map %s.trp in %s' % (transport.name, path))

    transport.lines = __load_transport_lines(ini)
    transport.transfers = __load_transfers(ini)
    return transport


def __get_transport_type(file_name, trp_name, ini):
    if not any(__TRANSPORT_TYPE_DICT):
        assets_path = os.path.join(os.path.dirname(__file__), 'assets')
        for line in read_all_lines(os.path.join(assets_path, 'transports.csv')):
            _file_name, _trp_name, _trp_type = as_quoted_list(line)
            __TRANSPORT_TYPE_DICT[_file_name + '.zip.' + _trp_name] = _trp_type

    trp_type = get_ini_attr(ini, 'Options', 'Type', None)
    if trp_type is not None:
        return trp_type

    dict_id = file_name + '.' + trp_name
    if dict_id in __TRANSPORT_TYPE_DICT:
        return __TRANSPORT_TYPE_DICT[dict_id]
    else:
        LOG.error('Unknown transport type for \'%s.trp\' in \'%s\', used defaults' % (trp_name, file_name))
        return __TRANSPORT_TYPE_DEFAULT


def __load_transfers(ini):
    section = get_ini_section(ini, 'Transfers')
    if section is None:
        return []

    transfers = []
    for name in section:
        if str(name).startswith('__'):
            continue

        line = section[name]
        params = as_quoted_list(line)
        from_line, from_station, to_line, to_station = params[:4]

        if len(params) > 4:
            delay = float(un_bugger_for_float(params[4]))
        else:
            delay = None

        if len(params) > 5:
            visibility = params[5]
        else:
            visibility = 'visible'
        transfers.append((from_line, from_station, to_line, to_station, delay, visibility))
    return transfers


def __load_transport_lines(ini):
    sections = get_ini_sections(ini, 'Line')
    if not any(sections):
        return []

    lines = []
    for section_name in sections:
        system_name = get_ini_attr(ini, section_name, 'Name')
        display_name = get_ini_attr(ini, section_name, 'Alias', system_name)

        line = MapTransportLine()
        line.alias = display_name
        line.name = system_name
        line.map = get_ini_attr(ini, section_name, 'LineMap')
        line.stations, line.segments = __parse_station_and_delays(
            get_ini_attr(ini, section_name, 'Stations'),
            get_ini_attr(ini, section_name, 'Driving'))

        line.aliases = __parse_aliases(get_ini_attr(ini, section_name, 'Aliases'))
        line.delays = __parse_line_delays(get_ini_attr_collection(ini, section_name, 'Delay'))
        lines.append(line)
    return lines


def __parse_aliases(aliases_text):
    if aliases_text is None or len(aliases_text) == 0:
        return dict()
    return as_dict(aliases_text)


def __parse_line_delays(delays_section):
    delays = {}
    if 'Delays' in delays_section:
        default_delays = as_delay_list(delays_section['Delays'])
        for i in range(len(default_delays)):
            delays[str(i)] = default_delays[i]
        del delays_section['Delays']

    for name in delays_section:
        delays[name[5:]] = delays_section[name]

    return delays


def __get_stations(stations_text):
    stations = []
    filtered = set()
    stations_iter = StationsString(stations_text)
    quoted = False
    while stations_iter.has_next():

        if stations_iter.next_separator == '(':
            quoted = True

        if stations_iter.next_separator == ')':
            quoted = False

        station = stations_iter.next()

        if station not in filtered and not quoted:
            filtered.add(station)
            stations.append(station)

    return stations


def __parse_station_and_delays(stations_text, drivings_text):
    stations_iter = StationsString(stations_text)
    delays_iter = DelaysString(drivings_text)

    stations = __get_stations(stations_text)

    if len(stations) < 2 and len(drivings_text) == 0:
        return stations, []

    segments = []

    from_station = None
    from_delay = None

    this_station = stations_iter.next()

    while True:
        if stations_iter.next_separator == '(':
            idx = 0
            delays = delays_iter.next_bracket()
            while stations_iter.has_next() and stations_iter.next_separator != ')':
                is_forward = True

                bracketed_station_name = stations_iter.next()
                if stations_iter.next_reverse:
                    is_forward = not is_forward

                if bracketed_station_name is not None and len(bracketed_station_name) > 0:
                    if idx < len(delays):
                        delay = delays[idx]
                    else:
                        delay = None

                    if is_forward:
                        segments.append(__create_segment(stations, this_station, bracketed_station_name, delay))
                    else:
                        segments.append(__create_segment(stations, bracketed_station_name, this_station, delay))
                idx += 1
            # /while
            from_station = this_station
            from_delay = None
            if not stations_iter.has_next():
                break

            this_station = stations_iter.next()
        else:
            to_station = stations_iter.next()

            if delays_iter.begin_bracket():
                delays = delays_iter.next_bracket()
                to_delay = delays[0]
                from_delay = delays[1]
            else:
                to_delay = delays_iter.next()

            this_from_segment = __create_segment(stations, this_station, from_station, from_delay)
            this_to_segment = __create_segment(stations, this_station, to_station, to_delay)

            if from_station is not None and __is_segment_not_exists(segments, this_from_segment):
                if from_delay is None:
                    opposite = __find_segment(segments, stations, from_station, this_station)
                    if opposite is not None:
                        this_from_segment = __create_segment(stations, this_station, from_station, opposite[2])
                segments.append(this_from_segment)
            if to_station is not None and not (this_to_segment in segments):
                segments.append(this_to_segment)

            from_station = this_station
            from_delay = to_delay
            this_station = to_station

            if not (stations_iter.has_next()):
                this_from_segment = __create_segment(stations, this_station, from_station, from_delay)
                if from_station is not None and __is_segment_not_exists(segments, this_from_segment):
                    if from_delay is None:
                        opposite = __find_segment(segments, stations, from_station, this_station)
                        if opposite is not None:
                            this_from_segment = __create_segment(stations, this_station, from_station, opposite[2])
                    segments.append(this_from_segment)

        if not (stations_iter.has_next()):
            break

    list.sort(segments)

    return stations, segments


def __create_segment(stations, from_station, to_station, delay):
    from_station, to_station = __get_segment_from_to(stations, from_station, to_station)
    return from_station, to_station, delay


def __find_segment(segments, stations, from_station, to_station):
    from_station, to_station = __get_segment_from_to(stations, from_station, to_station)
    for segment in segments:
        if segment[0] == from_station and segment[1] == to_station:
            return segment
    return None


def __is_segment_not_exists(segments, segment):
    from_station, to_station, delay = segment
    for segment in segments:
        if segment[0] == from_station and segment[1] == to_station:
            return False
    return True


def __get_segment_from_to(stations, from_station, to_station):
    if from_station is not None:
        from_station = stations.index(from_station)
    else:
        from_station = None
    if to_station is not None:
        to_station = stations.index(to_station)
    else:
        to_station = None
    return from_station, to_station


class DelaysString(object):
    def __init__(self, text):
        self.text = str(text)
        self.pos = 0
        if text is None:
            self.len = 0
        else:
            self.len = len(text)

    def begin_bracket(self):
        return self.text is not None and self.pos < self.len and self.text[self.pos] == '('

    def __next_block(self):
        if self.text is None:
            return None

        if self.begin_bracket():
            idx = self.text.find(')', self.pos)
        else:
            idx = self.pos

        next_comma = self.text.find(',', idx)
        if next_comma != -1:
            block = self.text[self.pos: next_comma]
            self.pos = next_comma + 1
        else:
            block = self.text[self.pos:]
            self.pos = self.len

        return block

    def next(self):
        next_value = self.__next_block()
        if not any(next_value):
            return None
        return float(next_value)

    def next_bracket(self):
        if self.text is None:
            return None
        delays = []
        for p in self.__next_block()[1:-1].split(','):
            delays.append(as_delay(p))
        return delays


class StationsString:
    def __init__(self, text):
        self.text = str(text)
        self.len = len(text)
        self.separators = ',()'
        self.pos = 0
        self.next_separator = ''
        self.next_reverse = False
        self.reset()

    def reset(self):
        self.pos = 0
        self.__skip_to_content()

    def at_next(self):
        if self.pos < self.len:
            return self.text[self.pos: self.pos + 1]
        else:
            return None

    def has_next(self):
        current = self.pos
        try:
            self.__skip_to_content()
            return not self.__eof()
        finally:
            self.pos = current

    def __eof(self):
        return self.pos >= self.len

    def next(self):
        self.__skip_to_content()
        if self.__eof():
            return ''
        current = self.pos
        symbol = None
        quotes = False
        while current < self.len:
            symbol = self.text[current:current + 1]
            if not (symbol not in self.separators or quotes):
                break

            if symbol == '"':
                quotes = not quotes
            current += 1

        if symbol is None:
            end = current - 1
        else:
            end = current

        self.next_separator = symbol
        txt = self.text[self.pos: end]
        self.pos = end

        self.next_reverse = False
        if txt.startswith('-'):
            self.next_reverse = True
            txt = txt[1:]

        if txt.startswith('"-'):
            self.next_reverse = True
            txt = '"' + txt[2:]

        return txt

    def __skip_to_content(self):
        symbol = self.at_next()
        while self.pos < self.len and symbol in self.separators:
            if symbol == '(':
                self.pos += 1
                return

            self.pos += 1
            symbol_next = self.at_next()

            if symbol == ',' and symbol_next != '(':
                return
            symbol = symbol_next
