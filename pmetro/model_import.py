from pmetro.files import find_files_by_extension
from pmetro.model_maps import load_schemes
from pmetro.model_objects import MapContainer
from pmetro.model_transports import load_transports
from pmetro.readers import deserialize_ini, get_ini_attr


def import_pmz_map(path):
    map_container = create_metadata(path)
    load_transports(map_container, path)
    load_schemes(map_container, path)
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


