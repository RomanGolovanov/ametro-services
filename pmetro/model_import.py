from pmetro.files import find_files_by_extension
from pmetro.helpers import as_list
from pmetro.model_metadata import load_metadata
from pmetro.model_schemes import load_schemes
from pmetro.model_objects import MapContainer, MapMetadata
from pmetro.model_static import load_static
from pmetro.model_transports import load_transports
from pmetro.ini_files import deserialize_ini, get_ini_attr


def import_pmz_map(path, map_info):
    map_container = MapContainer()
    map_container.meta = MapMetadata(map_info)

    global_names = load_transports(map_container, path)
    load_schemes(map_container, path, global_names)
    load_static(map_container, path)

    load_metadata(map_container, path, map_info)

    return map_container


