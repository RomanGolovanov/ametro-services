from pmetro.files import find_files_by_extension
from pmetro.helpers import as_list
from pmetro.ini_files import deserialize_ini
from pmetro.ini_files import get_ini_attr


def load_metadata(map_container, path, map_info):
    metadata_files = find_files_by_extension(path, '.cty')
    if not any(metadata_files):
        raise FileNotFoundError('Cannot found .cty file in %s' % path)

    metadata = deserialize_ini(sorted(metadata_files)[0])
    delays = as_list(get_ini_attr(metadata, 'Options', 'DelayNames', 'Day,Night'))

    __lower_all_names(map_container)

    map_container.meta.delays = delays
    map_container.meta.transport_types = list(set([trp.type for trp in map_container.transports]))
    map_container.meta.transports = list([__get_transport_meta(trp) for trp in map_container.transports])
    map_container.meta.schemes = list([__get_scheme_meta(scheme) for scheme in map_container.schemes])


def __lower_all_names(map_container):
    for scheme in map_container.schemes:
        scheme.name = scheme.name.lower()
        scheme.transports = [x.lower() for x in scheme.transports]
        scheme.default_transports = [x.lower() for x in scheme.default_transports]

    for transport in map_container.transports:
        transport.name = transport.name.lower()
        for line in transport.lines:
            if line.map is None:
                continue
            line.map = line.map.lower()


def __get_scheme_meta(scheme):
    return {
        'name': scheme.name.lower(),
        'file': 'schemes/' + scheme.name.lower() + '.json',
        'transports': scheme.transports,
        'default_transports': scheme.default_transports
    }


def __get_transport_meta(transport):
    return {
        'name': transport.name.lower(),
        'file': 'transports/' + transport.name.lower() + '.json',
        'type': transport.type
    }


def __get_scheme_file_name(name):
    return 'schemes/' + name.lower() + '.json'


def __get_transport_file_name(name):
    return 'schemes/' + name.lower() + '.json'