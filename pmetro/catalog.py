import codecs
from datetime import timedelta, date
import json
import os
import shutil
from time import sleep, mktime
from urllib.error import URLError
import urllib.request
import uuid
import sys
import xml.etree.ElementTree as ET

from globalization.provider import GeoNamesProvider
from pmetro.file_utils import unzip_file, zip_folder, find_file_by_extension
from pmetro.log import EmptyLog
from pmetro.ini_files import deserialize_ini, get_ini_attr
from pmetro.pmz_import import convert_map


DOWNLOAD_MAP_MAX_RETRIES = 5

IGNORE_MAP_LIST = [
    'Moscow3d.zip',
    'MoscowGrd.zip',
    'Moscow_skor.zip',
    'Moscow_pix.zip',
    'MoscowHistory.zip'
]

MAP_NAME_FIX = {
    'Athenas': 'Athens',
    'Bonn-Koln': 'Koln',
    'Kolkata(Calcutta)': 'Kolkata',
    'Minneapolis - St.Paul': 'Minneapolis',
    'Мiнск': 'Minsk'
}


class MapCatalog(object):
    def __init__(self, maps=None):
        if not maps:
            maps = []
        self.maps = maps

    def add(self, uid, file_name, size, timestamp):
        self.maps.append({
            'geoname_id': uid,
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
        dst_map['geoname_id'] = src_map['geoname_id']
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


class MapCache(object):
    def __init__(self, service_url, cache_path, temp_path, log=EmptyLog()):

        self.__download_chunk_size = 16 * 1024
        self.__service_url = service_url
        self.__cache_path = cache_path
        self.__index_path = os.path.join(cache_path, 'index.json')
        self.__log = log
        self.__temp_path = temp_path

    def refresh(self, force=False):
        remote_maps = list(self.__download_map_index())
        if force:
            old_catalog = MapCatalog()
        else:
            old_catalog = load_catalog(self.__index_path)

        geonames_provider = GeoNamesProvider()
        cache_catalog = MapCatalog()
        for new_map in remote_maps:
            old_map = old_catalog.find_by_file(new_map['file'])
            if old_map is None or old_map['timestamp'] < new_map['timestamp'] or old_map['size'] != new_map['size']:

                city_name = new_map['city']
                country_name = new_map['country']

                city_info = geonames_provider.find_city(city_name, country_name)
                if city_info is None:
                    self.__log.info('Not found %s, [%s]/[%s], skipped' % (new_map['file'], city_name, country_name))
                    continue

                self.__log.debug('Recognised %s,%s,%s in [%s]/[%s]' % (
                    city_info.geoname_id, city_info.name, city_info.country, city_name, country_name))

                downloading_map = {
                    'geoname_id': city_info.geoname_id,
                    'file': new_map['file'],
                    'size': new_map['size'],
                    'timestamp': new_map['timestamp'],
                    'map_id': None
                }

                self.__download_map(downloading_map)
                cache_catalog.add_map(downloading_map)
            else:
                self.__log.info('Map [%s] already downloaded.' % new_map['file'])
                cache_catalog.add_map(old_map)

        for old_map in old_catalog.maps:
            if not any([m for m in remote_maps if m['file'] == old_map['file']]):
                os.remove(os.path.join(self.__cache_path, old_map['file']))
                self.__log.warning('Map [%s] removed as obsolete.' % old_map['file'])

        cache_catalog.save(self.__index_path)

    def __download_map_index(self):

        xml_maps = urllib.request.urlopen(self.__service_url + 'Files.xml').read().decode('windows-1251')

        with codecs.open(os.path.join(self.__cache_path, "Files.xml"), 'w', 'utf-8') as f:
            f.write(xml_maps)

        for el in ET.fromstring(xml_maps):
            file_name = el.find('Zip').attrib['Name']
            if file_name in IGNORE_MAP_LIST:
                self.__log.info('Ignored [%s].' % file_name)
                continue

            city_name = el.find('City').attrib['CityName']
            country_name = el.find('City').attrib['Country']
            if country_name == ' Программа' or city_name == '':
                self.__log.info('Skipped %s, [%s]/[%s]' % (file_name, city_name, country_name))
                continue
            if city_name in MAP_NAME_FIX:
                city_name = MAP_NAME_FIX[city_name]

            size = int(el.find('Zip').attrib['Size'])
            timestamp = mktime((date(1899, 12, 30) + timedelta(days=int(el.find('Zip').attrib['Date']))).timetuple())
            yield {'file': file_name, 'size': size, 'timestamp': timestamp, 'city': city_name, 'country': country_name}

    def __download_map(self, map_item):
        map_file = map_item['file']
        tmp_path = os.path.join(self.__cache_path, map_file + '.download')
        map_path = os.path.join(self.__cache_path, map_file)

        retry = 0
        while retry < DOWNLOAD_MAP_MAX_RETRIES:
            retry += 1

            if os.path.isfile(tmp_path):
                os.remove(tmp_path)
            try:
                urllib.request.urlretrieve(self.__service_url + map_file, tmp_path)
            except URLError:
                self.__log.warning('Map [%s] download error, wait and retry.' % map_file)
                sleep(0.5)
                continue

            self.__fill_map_info(tmp_path, map_item)

            if os.path.isfile(map_path):
                os.remove(map_path)

            os.rename(tmp_path, map_path)
            self.__log.info('Downloaded [%s]' % map_file)
            return
        raise IOError('Max retries for downloading file [%s] reached. Terminate.' % map_file)

    def __fill_map_info(self, map_file, map_item):
        self.__log.info('Extract map info from [%s]' % map_file)
        temp_folder = os.path.join(self.__temp_path, uuid.uuid1().hex)
        try:
            unzip_file(map_file, temp_folder)
            pmz_file = find_file_by_extension(temp_folder, '.pmz')
            map_folder = pmz_file[0:-4]
            unzip_file(pmz_file, map_folder)

            self.__extract_map_id(map_folder, map_item)

        finally:
            shutil.rmtree(temp_folder)

    def __extract_map_id(self, map_folder, map_item):
        ini = deserialize_ini(find_file_by_extension(map_folder, '.cty'))
        name = get_ini_attr(ini, 'Options', 'Name')

        if name is None:
            name = uuid.uuid1().hex
            self.__log.warning('Empty NAME map property in file \'%s\', used UID %s' % (ini['__FILE_NAME__'], name))

        map_item['map_id'] = name


class MapImporter(object):
    def __init__(self, import_path, temp_path, log=EmptyLog()):
        self.__log = log
        self.__import_path = import_path
        self.__index_path = os.path.join(import_path, 'index.json')
        self.__timestamp_path = os.path.join(import_path, 'timestamp.json')
        self.__countries_path = os.path.join(import_path, 'countries.json')
        self.__temp_path = temp_path

    @staticmethod
    def __create_map_description(map_info_list):
        lst = sorted(map_info_list, key=lambda x: x['file'])
        max_timestamp = max([x['timestamp'] for x in lst])
        map_item = lst[0]
        map_item['timestamp'] = max_timestamp
        return map_item

    def import_maps(self, cache_path, force=False):
        new_catalog = load_catalog(os.path.join(cache_path, 'index.json'))
        old_catalog = load_catalog(self.__index_path)

        imported_catalog = MapCatalog()
        for map_id in sorted(set([m['map_id'] for m in new_catalog.maps])):
            cached_list = new_catalog.find_list_by_id(map_id)
            cached_file_list = [x['file'] for x in cached_list]

            new_map = MapImporter.__create_map_description(cached_list)
            map_file = new_map['file']
            old_map = old_catalog.find_by_file(map_file)

            if not force and old_map is not None and old_map['timestamp'] == new_map['timestamp']:
                self.__log.info('Maps [%s] already imported as [%s].' % (cached_file_list, map_file))
                imported_catalog.add_map(old_map)
                continue

            # noinspection PyBroadException
            try:
                self.__import_maps(cache_path, cached_list, new_map)
                self.__log.info('Map(s) [%s] imported as [%s].' % (cached_file_list, map_file))
                imported_catalog.add_map(new_map)
            except:
                self.__log.error('Map [%s] import skipped due error %s.' % (map_file, sys.exc_info()))

        imported_catalog.save(self.__index_path)
        imported_catalog.save_timestamp(self.__timestamp_path)

    def __import_maps(self, cache_path, src_map_list, map_info):
        importing_map_path = os.path.join(self.__import_path, map_info['file'])
        temp_root = self.__create_tmp()
        try:
            map_folder = os.path.join(temp_root, map_info['map_id'])
            os.mkdir(map_folder)
            for src_zip_with_pmz in [os.path.join(cache_path, x['file']) for x in src_map_list]:
                tmp_folder = self.__extract_pmz(
                    src_zip_with_pmz,
                    self.__create_tmp(temp_root),
                    self.__create_tmp(temp_root))
                self.__move_map_files(tmp_folder, map_folder)

            converted_folder = map_folder + '.converted'
            if not os.path.isdir(converted_folder):
                os.mkdir(converted_folder)

            convert_map(map_info['geoname_id'], map_info['file'], map_info['timestamp'], map_folder, converted_folder,
                        self.__log)

            zip_folder(converted_folder, importing_map_path)
            map_info['size'] = os.path.getsize(importing_map_path)

        finally:
            shutil.rmtree(temp_root)

    def __move_map_files(self, src_path, dst_path):
        for file_name in os.listdir(src_path):
            src = os.path.join(src_path, file_name)
            dst = os.path.join(dst_path, file_name)
            if not os.path.isfile(dst):
                shutil.move(src, dst)
            else:
                self.__log.warning("File name %s already exists in map directory, skipped" % file_name)

    def __extract_pmz(self, src_zip_with_pmz, temp_folder, map_folder):
        extract_folder = self.__create_tmp(temp_folder)
        unzip_file(src_zip_with_pmz, extract_folder)
        pmz_file = find_file_by_extension(extract_folder, '.pmz')
        unzip_file(pmz_file, map_folder)
        return map_folder

    def __create_tmp(self, root_folder=None, create=True):
        if root_folder is None:
            root_folder = self.__temp_path
        tmp_folder = os.path.join(root_folder, uuid.uuid1().hex)
        if create:
            os.mkdir(tmp_folder)
        return tmp_folder