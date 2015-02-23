from pmetro.files import find_files_by_extension
from pmetro.helpers import as_list
from pmetro.model_maps import load_schemes
from pmetro.model_objects import MapContainer, MapMetadata
from pmetro.model_transports import load_transports
from pmetro.readers import deserialize_ini, get_ini_attr


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

    map_container.meta.transport_types = list(set([trp.type for trp in map_container.transports]))
    map_container.meta.transports = list([trp.name for trp in map_container.transports])
    map_container.meta.schemes = list([scheme.name for scheme in map_container.schemes])

    return map_container

