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
from pmetro.ini_files import deserialize_ini, get_ini_attr, get_ini_composite_attr
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

    def add(self, uid, city, country, iso, latitude, longitude, file_name, size, timestamp, version):
        self.maps.append({
            'id': uid,
            'city': city,
            'iso': iso,
            'country': country,
            'latitude': latitude,
            'longitude': longitude,
            'file': file_name,
            'size': size,
            'timestamp': timestamp,
            'version': version,
            'comments': None,
            'description': None,
            'map_id': None
        })

    def add_map(self, map_info):
        self.maps.append(map_info)

    def save(self, path):
        with codecs.open(path, 'w', 'utf-8') as f:
            f.write(
                json.dumps({'maps': self.maps, 'version': self.get_version()}, ensure_ascii=False, indent=4))

    def save_version(self, path):
        with codecs.open(path, 'w', 'utf-8') as f:
            f.write(
                json.dumps({'version': self.get_version()}, ensure_ascii=False, indent=4))

    def save_countries(self, path):
        country_iso_dict = {}
        for m in self.maps:
            country_name = m['country']
            country_iso = m['iso']
            country_iso_dict[country_name] = country_iso
        with codecs.open(path, 'w', 'utf-8') as f:
            f.write(
                json.dumps(country_iso_dict, ensure_ascii=False, indent=4))

    def load(self, path):
        with codecs.open(path, 'r', 'utf-8') as f:
            self.maps = json.load(f)['maps']

    def get_version(self):
        version = 0
        for m in self.maps:
            if version is None or version < m['version']:
                version = m['version']
        return version

    def get_json(self):
        return json.dumps({'maps': self.maps, 'version': self.get_version()}, ensure_ascii=False)

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
        dst_map['id'] = src_map['id']
        dst_map['city'] = src_map['city']
        dst_map['map_id'] = src_map['map_id']
        dst_map['description'] = src_map['description']
        dst_map['comments'] = src_map['comments']
        dst_map['iso'] = src_map['iso']
        dst_map['country'] = src_map['country']
        dst_map['latitude'] = src_map['latitude']
        dst_map['longitude'] = src_map['longitude']
        dst_map['file'] = src_map['file']
        dst_map['size'] = src_map['size']
        dst_map['timestamp'] = src_map['timestamp']
        dst_map['version'] = src_map['version']


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
        if not os.path.isdir(self.__temp_path):
            os.mkdir(self.__temp_path)

        if not os.path.isdir(self.__cache_path):
            os.mkdir(self.__cache_path)

    def refresh(self, force=False):
        new_catalog = self.__download_map_index()
        if force:
            old_catalog = MapCatalog()
        else:
            old_catalog = load_catalog(self.__index_path)

        cache_catalog = MapCatalog()
        for new_map in new_catalog.maps:
            old_map = old_catalog.find_by_file(new_map['file'])
            if old_map is None or old_map['version'] < new_map['version'] or old_map['size'] != new_map['size']:
                self.__download_map(new_map)
                cache_catalog.add_map(new_map)
            else:
                self.__log.info('Map [%s] already downloaded.' % new_map['file'])
                cache_catalog.add_map(old_map)

        for old_map in old_catalog.maps:
            new_map = new_catalog.find_by_file(old_map['file'])
            if new_map is None:
                os.remove(os.path.join(self.__cache_path, old_map['file']))
                self.__log.info('Map [%s] removed as obsolete.' % old_map['file'])

        cache_catalog.save(self.__index_path)

    def __download_map_index(self):
        geonames_provider = GeoNamesProvider()

        xml_maps = urllib.request.urlopen(self.__service_url + 'Files.xml').read().decode('windows-1251')

        with codecs.open(os.path.join(self.__cache_path, "Files.xml"), 'w', 'utf-8') as f:
            f.write(xml_maps)

        catalog = MapCatalog()
        for el in ET.fromstring(xml_maps):
            city_name = el.find('City').attrib['CityName']
            country_name = el.find('City').attrib['Country']
            file_name = el.find('Zip').attrib['Name']
            size = int(el.find('Zip').attrib['Size'])
            version = int(el.find('Zip').attrib['Date'])
            timestamp = mktime((date(1899, 12, 30) + timedelta(days=version)).timetuple())

            if file_name in IGNORE_MAP_LIST:
                self.__log.info('Ignored [%s].' % file_name)
                continue

            if country_name == ' Программа' or city_name == '':
                self.__log.info('Skipped %s, [%s]/[%s]' % (file_name, city_name, country_name))
                continue

            if city_name in MAP_NAME_FIX:
                city_name = MAP_NAME_FIX[city_name]

            city = geonames_provider.find_city(city_name, country_name)
            if city is None:
                self.__log.info('Not found %s, [%s]/[%s]' % (file_name, city_name, country_name))
                continue

            self.__log.debug('Recognised %s,%s,%s in [%s]/[%s]' % (
                city.geoname_id, city.name, city.country, city_name, country_name))

            catalog.add(
                city.geoname_id,
                city.name,
                city.country,
                city.iso,
                city.latitude,
                city.longitude,
                file_name,
                size,
                timestamp,
                version)

        return catalog

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

            self.__extract_map_info(map_folder, map_item)

        finally:
            shutil.rmtree(temp_folder)

    def __extract_map_info(self, map_folder, map_item):
        ini = deserialize_ini(find_file_by_extension(map_folder, '.cty'))
        name = get_ini_attr(ini, 'Options', 'Name')
        comments = get_ini_composite_attr(ini, 'Options', 'Comment')
        authors = get_ini_composite_attr(ini, 'Options', 'MapAuthors')

        if name is None:
            name = uuid.uuid1().hex
            self.__log.warning('Empty NAME map property in file \'%s\', used UID %s' % (ini['__FILE_NAME__'], name))

        map_item['map_id'] = name
        if comments is not None:
            map_item['comments'] = comments
        if authors is not None:
            map_item['description'] = authors


class MapImporter(object):
    def __init__(self, import_path, temp_path, log=EmptyLog()):
        self.__log = log
        self.__import_path = import_path
        self.__index_path = os.path.join(import_path, 'index.json')
        self.__version_path = os.path.join(import_path, 'version.json')
        self.__countries_path = os.path.join(import_path, 'countries.json')
        self.__temp_path = temp_path

        if not os.path.isdir(self.__temp_path):
            os.mkdir(self.__temp_path)

        if not os.path.isdir(self.__import_path):
            os.mkdir(self.__import_path)

    @staticmethod
    def __create_map_description(map_info_list):
        lst = sorted(map_info_list, key=lambda x: x['file'])
        max_version = max([x['version'] for x in lst])
        map_item = lst[0]
        map_item['version'] = max_version
        return map_item

    def import_maps(self, cache_path, force=False):
        new_catalog = load_catalog(os.path.join(cache_path, 'index.json'))
        old_catalog = load_catalog(self.__index_path)

        published_catalog = MapCatalog()
        for map_id in sorted(set([m['map_id'] for m in new_catalog.maps])):
            cached_list = new_catalog.find_list_by_id(map_id)
            cached_file_list = [x['file'] for x in cached_list]

            new_map = MapImporter.__create_map_description(cached_list)
            map_file = new_map['file']
            old_map = old_catalog.find_by_file(map_file)

            if not force and old_map is not None and old_map['version'] == new_map['version']:
                self.__log.info('Maps [%s] already published as [%s].' % (cached_file_list, map_file))
                published_catalog.add_map(old_map)
                continue

            # noinspection PyBroadException
            try:
                self.__import_maps(cache_path, cached_list, new_map)
                self.__log.info('Map(s) [%s] imported as [%s].' % (cached_file_list, map_file))
                published_catalog.add_map(new_map)
            except:
                self.__log.error('Map [%s] import skipped due error %s.' % (map_file, sys.exc_info()))

        published_catalog.save(self.__index_path)
        published_catalog.save_version(self.__version_path)
        published_catalog.save_countries(self.__countries_path)

    def __import_maps(self, cache_path, src_map_list, map_info):
        publication_map_path = os.path.join(self.__import_path, map_info['file'])
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

            convert_map(map_info, map_folder, map_folder + '.converted', self.__log)

            zip_folder(map_folder + '.converted', publication_map_path)
            map_info['size'] = os.path.getsize(publication_map_path)

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