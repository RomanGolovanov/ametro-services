import codecs
import json


class MapCatalog(object):
    def __init__(self, maps=None):
        if not maps:
            maps = []
        self.maps = maps

    def add(self, uid, file_name, size, timestamp):
        self.maps.append({
            'city_id': uid,
            'file': file_name,
            'size': size,
            'timestamp': timestamp,
            'map_id': None
        })

    def add_map(self, map_info):
        self.maps.append(map_info)

    def save(self, path):
        with codecs.open(path, 'w', 'utf-8') as f:
            f.write(
                json.dumps({'maps': self.maps, 'timestamp': self.get_timestamp()}, ensure_ascii=False, indent=4))

    def save_timestamp(self, path):
        with codecs.open(path, 'w', 'utf-8') as f:
            f.write(
                json.dumps({'timestamp': self.get_timestamp()}, ensure_ascii=False, indent=4))

    def load(self, path):
        with codecs.open(path, 'r', 'utf-8') as f:
            self.maps = json.load(f)['maps']

    def get_timestamp(self):
        timestamp = 0
        for m in self.maps:
            if timestamp is None or timestamp < m['timestamp']:
                timestamp = m['timestamp']
        return timestamp

    def get_json(self):
        return json.dumps({'maps': self.maps, 'timestamp': self.get_timestamp()}, ensure_ascii=False)

    def find_by_file(self, file_name):
        for m in self.maps:
            if m['file'] == file_name:
                return m

    def find_list_by_id(self, map_id):
        lst = []
        for m in self.maps:
            if m['map_id'] == map_id:
                lst.append(m)
        return lst

    @staticmethod
    def clone(src_map):
        cloned_map = {}
        MapCatalog.copy(src_map, cloned_map)
        return cloned_map

    @staticmethod
    def copy(src_map, dst_map):
        dst_map['city_id'] = src_map['city_id']
        dst_map['map_id'] = src_map['map_id']
        dst_map['file'] = src_map['file']
        dst_map['size'] = src_map['size']
        dst_map['timestamp'] = src_map['timestamp']


def load_catalog(path):
    catalog = MapCatalog()
    # noinspection PyBroadException
    try:
        catalog.load(path)
    except:
        catalog = MapCatalog()
    return catalog

