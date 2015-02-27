from pmetro.files import find_files_by_extension
from pmetro.helpers import as_list
from pmetro.model_schemes import load_schemes
from pmetro.model_objects import MapContainer, MapMetadata
from pmetro.model_static import load_static
from pmetro.model_transports import load_transports
from pmetro.ini_files import deserialize_ini, get_ini_attr


def import_pmz_map(path, map_info):
    metadata_files = find_files_by_extension(path, '.cty')
    if not any(metadata_files):
        raise FileNotFoundError('Cannot found .cty file in %s' % path)

    metadata = deserialize_ini(sorted(metadata_files)[0])
    delays = as_list(get_ini_attr(metadata, 'Options', 'DelayNames', 'Day,Night'))

    map_container = MapContainer()
    map_container.meta = MapMetadata(map_info, delays)

    load_transports(map_container, path)
    load_schemes(map_container, path)
    load_static(map_container, path)

    map_container.meta.transport_types = list(set([trp.type for trp in map_container.transports]))
    map_container.meta.transports = list([trp.name for trp in map_container.transports])
    map_container.meta.schemes = list([scheme.name for scheme in map_container.schemes])

    __lower_all_names(map_container)

    return map_container


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

    map_container.meta.transports = [x.lower() for x in map_container.meta.transports]
    map_container.meta.schemes = [x.lower() for x in map_container.meta.schemes]

