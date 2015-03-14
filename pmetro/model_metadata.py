from pmetro.files import find_files_by_extension
from pmetro.helpers import as_list
from pmetro.ini_files import deserialize_ini
from pmetro.ini_files import get_ini_attr


def load_metadata(map_container, path):
    metadata_files = find_files_by_extension(path, '.cty')
    if not any(metadata_files):
        raise FileNotFoundError('Cannot found .cty file in %s' % path)

    metadata = deserialize_ini(sorted(metadata_files)[0])
    delays = as_list(get_ini_attr(metadata, 'Options', 'DelayNames', 'Day,Night'))

    map_container.meta.delays = delays
    map_container.meta.transport_types = list(set([trp.type for trp in map_container.transports]))
    map_container.meta.transports = list([__get_transport_meta(trp) for trp in map_container.transports])

    child_schemes = __get_child_schemes(map_container)
    map_container.meta.schemes = list([__get_scheme_meta(scheme, child_schemes) for scheme in map_container.schemes])


def __get_child_schemes(map_container):
    children = set()
    for transport in map_container.transports:
        for line in transport.lines:
            if line.scheme is None:
                continue
            children.add(line.scheme)
    return children

def __get_scheme_meta(scheme, child_schemes):
    return {
        'name': scheme.name,
        'file': 'schemes/' + scheme.name + '.json',
        'transports': scheme.transports,
        'default_transports': scheme.default_transports,
        'root': scheme.name not in child_schemes,
        'display_name': scheme.display_name,
        'type_name': scheme.type_name,
    }


def __get_transport_meta(transport):
    return {
        'name': transport.name,
        'file': 'transports/' + transport.name + '.json',
        'type': transport.type
    }


def __get_scheme_file_name(name):
    return 'schemes/' + name + '.json'


def __get_transport_file_name(name):
    return 'schemes/' + name + '.json'