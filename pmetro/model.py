import os

from pmetro.files import find_files_by_extension, get_file_name_without_ext
from pmetro.helpers import as_list, as_delay_list
from pmetro.model_helpers import parse_station_and_delays
from pmetro.readers import deserialize_ini, get_ini_attr, get_ini_section, get_ini_sections


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
        from_line, from_station, to_line, to_station = params[:4]
        delay = float(params[4])
        if len(params) > 5:
            state = params[5]
        else:
            state = 'visible'

        transfers.append((from_line, from_station, to_line, to_station, delay, state))

    return transfers


def load_lines(ini):
    sections = get_ini_sections(ini, 'Line')
    if not any(sections):
        return []

    lines = []
    for section_name in sections:

        system_name = get_ini_attr(ini, section_name, 'Name')
        display_name = get_ini_attr(ini, section_name, 'Alias', system_name)

        line = MapLine()
        line.name = display_name
        line.id = system_name
        line.map = get_ini_attr(ini, section_name, 'LineMap')
        line.stations, line.segments = parse_station_and_delays(
            get_ini_attr(ini, section_name, 'Stations'),
            get_ini_attr(ini, section_name, 'Driving'))

        line.aliases = get_ini_attr(ini, section_name, 'Aliases')
        line.delays = as_delay_list(get_ini_attr(ini, section_name, 'Delays'))
        lines.append(line)
    return lines


