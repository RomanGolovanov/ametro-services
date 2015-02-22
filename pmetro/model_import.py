import os

from pmetro.files import find_files_by_extension, get_file_name_without_ext
from pmetro.helpers import as_delay_list, as_quoted_list, un_bugger_for_float
from pmetro.model_helpers import parse_station_and_delays
from pmetro.model_objects import MapContainer, MapTransport, MapTransfer, MapLine
from pmetro.readers import deserialize_ini, get_ini_attr, get_ini_section, get_ini_sections, get_ini_attr_collection


def import_pmz_map(path):
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

        line_list = section[name].split('\n')
        for line in line_list:
            params = as_quoted_list(line)
            from_line, from_station, to_line, to_station = params[:4]
            if len(params) > 4:
                delay = float(un_bugger_for_float(params[4]))
            else:
                delay = None

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
        line.delays = parse_line_delays(get_ini_attr_collection(ini, section_name, 'Delay'))
        lines.append(line)
    return lines


def parse_line_delays(delays_section):
    delays = {}
    if 'Delays' in delays_section:
        default_delays = as_delay_list(delays_section['Delays'])
        for i in range(len(default_delays)):
            delays[str(i)] = default_delays[i]
        del delays_section['Delays']

    for name in delays_section:
        delays[name[5:]] = delays_section[name]

    return delays