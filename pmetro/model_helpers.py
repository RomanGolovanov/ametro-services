from pmetro.helpers import as_delay, as_quoted_list


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
        self.reset()

    def reset(self):
        self.pos = 0
        self.skip_to_content()

    def at_next(self):
        if self.pos < self.len:
            return self.text[self.pos: self.pos + 1]
        else:
            return None

    def has_next(self):
        current = self.pos
        try:
            self.skip_to_content()
            return not self.__eof()
        finally:
            self.pos = current

    def __eof(self):
        return self.pos >= self.len

    def next(self):
        self.skip_to_content()
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
        return txt

    def skip_to_content(self):
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


def get_stations(stations_text):
    cleared_text = stations_text.replace('(', ',').replace(')', ',')
    stations = as_quoted_list(cleared_text)
    stations = list(set(stations))
    list.sort(stations)
    return stations


def parse_station_and_delays(stations_text, drivings_text):
    stations_iter = StationsString(stations_text)
    delays_iter = DelaysString(drivings_text)

    stations = get_stations(stations_text)

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
                if bracketed_station_name.startswith('-'):
                    bracketed_station_name = bracketed_station_name[1:]
                    is_forward = not is_forward

                if bracketed_station_name is not None and len(bracketed_station_name) > 0:
                    if idx < len(delays):
                        delay = delays[idx]
                    else:
                        delay = None

                    if is_forward:
                        segments.append(create_segment(stations, this_station, bracketed_station_name, delay))
                    else:
                        segments.append(create_segment(stations, bracketed_station_name, this_station, delay))
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

            this_from_segment = create_segment(stations, this_station, from_station, from_delay)
            this_to_segment = create_segment(stations, this_station, to_station, to_delay)

            if from_station is not None and segment_not_exists(segments, this_from_segment):
                if from_delay is None:
                    opposite = find_segment(segments, stations, from_station, this_station)
                    if opposite is not None:
                        this_from_segment = create_segment(stations, this_station, from_station, opposite[2])
                segments.append(this_from_segment)
            if to_station is not None and not (this_to_segment in segments):
                segments.append(this_to_segment)

            from_station = this_station
            from_delay = to_delay
            this_station = to_station

            if not (stations_iter.has_next()):
                this_from_segment = create_segment(stations, this_station, from_station, from_delay)
                if from_station is not None and segment_not_exists(segments, this_from_segment):
                    if from_delay is None:
                        opposite = find_segment(segments, stations, from_station, this_station)
                        if opposite is not None:
                            this_from_segment = create_segment(stations, this_station, from_station, opposite[2])
                    segments.append(this_from_segment)

        if not (stations_iter.has_next()):
            break

    list.sort(segments)

    return stations, segments


def create_segment(stations, from_station, to_station, delay):
    from_station, to_station = get_segment_from_to(stations, from_station, to_station)
    return from_station, to_station, delay


def find_segment(segments, stations, from_station, to_station):
    from_station, to_station = get_segment_from_to(stations, from_station, to_station)
    for segment in segments:
        if segment[0] == from_station and segment[1] == to_station:
            return segment
    return None


def segment_not_exists(segments, segment):
    from_station, to_station, delay = segment
    for segment in segments:
        if segment[0] == from_station and segment[1] == to_station:
            return False
    return True


def get_segment_from_to(stations, from_station, to_station):
    if from_station is not None:
        from_station = stations.index(from_station)
    else:
        from_station = None
    if to_station is not None:
        to_station = stations.index(to_station)
    else:
        to_station = None
    return from_station, to_station



