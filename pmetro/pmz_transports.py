import codecs
import os

from pmetro.helpers import as_delay_list, as_quoted_list, as_delay
from pmetro.log import ConsoleLog
from pmetro.ini_files import get_ini_attr


LOG = ConsoleLog()

__TRANSPORT_TYPE_DICT = {}
__TRANSPORT_TYPE_DEFAULT = 'Метро'

__DELAYS_TYPES = {
    'DelayDay': 0,
    'DelayNight': 1
}


def get_transport_type(file_name, trp_name, ini):
    if not any(__TRANSPORT_TYPE_DICT):
        assets_path = os.path.join(os.path.dirname(__file__), 'assets')
        with codecs.open(os.path.join(assets_path, 'transports.csv'), 'rU', encoding='utf-8') as f:
            for line in f:
                _file_name, _trp_name, _trp_type = as_quoted_list(line)
                __TRANSPORT_TYPE_DICT[
                    _file_name.lower().strip() + '.zip.' + _trp_name.lower().strip()] = _trp_type.strip('\r\n').strip()

    trp_type = get_ini_attr(ini, 'Options', 'Type', None)
    if trp_type is not None:
        return trp_type

    dict_id = file_name.lower() + '.' + trp_name.lower()
    if dict_id in __TRANSPORT_TYPE_DICT:
        return __TRANSPORT_TYPE_DICT[dict_id]
    else:
        LOG.error('Unknown transport type for \'%s.trp\' in \'%s\', used defaults' % (trp_name, file_name))
        return __TRANSPORT_TYPE_DEFAULT


def parse_line_delays(line_name, delays_section):
    if 'Delays' in delays_section:
        if len(delays_section.items()) > 1:
            LOG.error("Line \'{0}\' contains both Delays and Delay* parameters: {1}, used value from Delays".format(
                line_name,
                delays_section))
        return dict([(key, value) for key, value in enumerate(as_delay_list(delays_section['Delays']))])

    delays = {}
    for name in delays_section:
        if name not in __DELAYS_TYPES:
            LOG.error("Line \'{0}\' contains unknown parameter {1}, ignored".format(line_name, name))
            continue

        delays[__DELAYS_TYPES[name]] = delays_section[name]
    return delays


def get_stations(stations_text):
    stations = []
    stations_iter = StationsString(stations_text)
    quoted = False
    while stations_iter.has_next():

        if stations_iter.next_separator == '(':
            quoted = True

        if stations_iter.next_separator == ')':
            quoted = False

        station, original_station = stations_iter.next()

        if not quoted:
            stations.append(station)

    return stations


def parse_station_and_delays(stations_text, drivings_text):
    stations = get_stations(stations_text)
    if len(stations) < 2 and len(drivings_text) == 0:
        return stations, []

    segments = []

    delays_iter = DelaysString(drivings_text)
    stations_iter = StationsString(stations_text)

    from_station = None
    from_delay = None
    this_station, original_station = stations_iter.next()
    while True:
        if stations_iter.next_separator == '(':
            idx = 0
            delays = delays_iter.next_bracket()
            while stations_iter.has_next() and stations_iter.next_separator != ')':
                is_forward = True

                bracketed_station_name, original_station = stations_iter.next()
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

            this_station, original_station = stations_iter.next()
        else:
            to_station, original_station = stations_iter.next()

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
        return as_delay(next_value)

    def next_bracket(self):
        if self.text is None:
            return None
        delays = []
        for p in self.__next_block()[1:-1].split(','):
            delays.append(as_delay(p))
        return delays


class StationsString(object):
    def __init__(self, text):
        self.text = str(text)
        self.len = len(text)
        self.separators = ',()'
        self.pos = 0
        self.next_separator = ''
        self.next_reverse = False
        self.quoted = False
        self.reset()

        self.filtered = []

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
        if self.next_separator == '(':
            self.quoted = True
        if self.next_separator == ')':
            self.quoted = False

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

        original_txt = txt

        if not self.quoted:
            if txt in self.filtered:
                counter = 1
                name = '%s:X:%s' % (txt, counter)
                while name in self.filtered:
                    counter += 1
                    name = '%s:X:%s' % (txt, counter)

                LOG.error('Station \'%s\' already been found, used \'%s\'.' % (txt, name))
                txt = name
            self.filtered.append(txt)

        return txt, original_txt

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
