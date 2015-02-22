import codecs
import json
import os
import shutil
from time import sleep
from urllib.error import URLError
import urllib.request
import uuid
import sys
import xml.etree.ElementTree as ET

from globalization.GeoNames import GeoNamesProvider
from pmetro.files import unzip_file, zip_folder, find_file_by_extension
from pmetro.log import EmptyLog
from pmetro.map import convert_map
from pmetro.readers import IniReader

DOWNLOAD_MAP_MAX_RETRIES = 5


class MapCatalog(object):
    def __init__(self, maps=None):
        if not maps:
            maps = []
        self.maps = maps

    def add(self, uid, city, country, iso, latitude, longitude, file_name, size, version):
        self.maps.append({
            'id': uid,
            'city': city,
            'iso': iso,
            'country': country,
            'latitude': latitude,
            'longitude': longitude,
            'file': file_name,
            'size': size,
            'version': version,
            'comments': None,
            'description': None,
            'map_id': None
        })

    def save(self, path):
        with codecs.open(path, 'w', 'utf-8') as f:
            f.write(
                json.dumps({'maps': self.maps, 'version': self.get_version()}, ensure_ascii=False, indent=True))

    def save_version(self, path):
        with codecs.open(path, 'w', 'utf-8') as f:
            f.write(
                json.dumps({'version': self.get_version()}, ensure_ascii=False, indent=True))

    def save_countries(self, path):
        country_iso_dict = {}
        for m in self.maps:
            country_name = m['country']
            country_iso = m['iso']
            country_iso_dict[country_name] = country_iso
        with codecs.open(path, 'w', 'utf-8') as f:
            f.write(
                json.dumps(country_iso_dict, ensure_ascii=False, indent=True))

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
        return json.dumps({'maps': self.maps, 'version': self.get_version()}, ensure_ascii=False, indent=True)

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
        cloned_map = {
            'id': src_map['id'],
            'city': src_map['city'],
            'map_id': src_map['map_id'],
            'description': src_map['description'],
            'comments': src_map['comments'],
            'iso': src_map['iso'],
            'country': src_map['country'],
            'latitude': src_map['latitude'],
            'longitude': src_map['longitude'],
            'file': src_map['file'],
            'size': src_map['size'],
            'version': src_map['version']
        }
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
        dst_map['version'] = src_map['version']

    def add_map(self, map_info):
        self.maps.append(map_info)


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

        self.ignore_list = [
            'Moscow3d.zip',
            'MoscowGrd.zip',
            'Moscow_skor.zip',
            'Moscow_pix.zip',
            'MoscowHistory.zip'
        ]

        self.download_chunk_size = 16 * 1024
        self.service_url = service_url
        self.cache_path = cache_path
        self.cache_index_path = os.path.join(cache_path, 'index.json')
        self.log = log

        self.temp_path = temp_path
        if not os.path.isdir(temp_path):
            os.mkdir(temp_path)

        if not os.path.isdir(cache_path):
            os.mkdir(cache_path)

    def refresh(self, force=False):
        new_catalog = self.__download_map_index()
        old_catalog = load_catalog(self.cache_index_path)

        for new_map in new_catalog.maps:
            old_map = old_catalog.find_by_file(new_map['file'])
            if old_map is None or old_map['version'] < new_map['version'] or old_map['size'] != new_map['size']:
                self.__download_map(new_map)
            else:
                self.log.info('Map [%s] already downloaded.' % new_map['file'])
                MapCatalog.copy(old_map, new_map)

        for old_map in old_catalog.maps:
            new_map = new_catalog.find_by_file(old_map['file'])
            if new_map is None:
                os.remove(os.path.join(self.cache_path, old_map['file']))
                self.log.info('Map [%s] removed as obsolete.' % old_map['file'])

        new_catalog.save(self.cache_index_path)

    def __download_map_index(self):
        geonames_provider = GeoNamesProvider()

        xml_maps = urllib.request.urlopen(self.service_url + 'Files.xml').read().decode('windows-1251')

        catalog = MapCatalog()
        for el in ET.fromstring(xml_maps):
            city_name = el.find('City').attrib['CityName']
            country_name = el.find('City').attrib['Country']
            file_name = el.find('Zip').attrib['Name']
            size = int(el.find('Zip').attrib['Size'])
            version = int(el.find('Zip').attrib['Date'])

            if file_name in self.ignore_list:
                self.log.info('Ignored [%s].' % file_name)
                continue

            if country_name == ' Программа' or city_name == '':
                self.log.info('Skipped %s, [%s]/[%s]' % (file_name, city_name, country_name))
                continue

            city = geonames_provider.find_city(city_name, country_name)
            if city is None:
                self.log.info('Not found %s, [%s]/[%s]' % (file_name, city_name, country_name))
                continue

            catalog.add(
                city.Uid,
                city.Name,
                geonames_provider.get_country_name_by_iso(city.CountryIso),
                city.CountryIso,
                city.Latitude,
                city.Longitude,
                file_name,
                size,
                version)

        return catalog

    def __download_map(self, map_item):
        map_file = map_item['file']
        tmp_path = os.path.join(self.cache_path, map_file + '.download')
        map_path = os.path.join(self.cache_path, map_file)

        retry = 0
        while retry < DOWNLOAD_MAP_MAX_RETRIES:
            retry += 1

            if os.path.isfile(tmp_path):
                os.remove(tmp_path)
            try:
                urllib.request.urlretrieve(self.service_url + map_file, tmp_path)
            except URLError:
                self.log.debug('Map [%s] download error, wait and retry.' % map_file)
                sleep(0.5)
                continue

            self.__fill_map_info(tmp_path, map_item)

            if os.path.isfile(map_path):
                os.remove(map_path)

            os.rename(tmp_path, map_path)
            self.log.info('Downloaded [%s]' % map_file)
            return
        raise IOError('Max retries for downloading file [%s] reached. Terminate.' % map_file)

    def __fill_map_info(self, map_file, map_item):
        self.log.info('Extract map info from [%s]' % map_file)
        temp_folder = os.path.join(self.temp_path, uuid.uuid1().hex)
        try:
            unzip_file(map_file, temp_folder)
            pmz_file = find_file_by_extension(temp_folder, '.pmz')
            map_folder = pmz_file[0:-4]
            unzip_file(pmz_file, map_folder)

            self.__extract_map_info(map_folder, map_item)

        finally:
            shutil.rmtree(temp_folder)

    @staticmethod
    def __extract_map_info(map_folder, map_item):
        reader = IniReader()
        reader.open(find_file_by_extension(map_folder, '.cty'))

        reader.section('Options')

        map_id = uuid.uuid1().hex
        comments = []
        description = []
        while reader.read():
            if reader.name() == 'name':
                map_id = reader.value()
            if reader.name() == 'comment':
                comments.append(reader.value().replace('\\n', '\n').rstrip())
            if reader.name() == 'mapauthors':
                description.append(reader.value().replace('\\n', '\n').rstrip())
        map_item['map_id'] = map_id
        if any(comments):
            map_item['comments'] = '\n'.join(comments).rstrip('\n')
        if any(description):
            map_item['description'] = '\n'.join(description).rstrip('\n')


class MapPublication(object):
    def __init__(self, publication_path, temp_path, log=EmptyLog()):
        self.log = log
        self.publication_path = publication_path
        self.publication_index_path = os.path.join(publication_path, 'index.json')
        self.publication_version_path = os.path.join(publication_path, 'version.json')
        self.publication_countries_path = os.path.join(publication_path, 'countries.json')
        self.temp_path = temp_path
        if not os.path.isdir(temp_path):
            os.mkdir(temp_path)
        if not os.path.isdir(publication_path):
            os.mkdir(publication_path)

    @staticmethod
    def __create_map_description(map_info_list):
        lst = sorted(map_info_list, key=lambda x: x['file'])
        max_version = max([x['version'] for x in lst])
        map_item = MapCatalog.clone(lst[0])
        map_item['version'] = max_version
        return map_item

    def import_maps(self, cache_path, force=False):
        cached_catalog = load_catalog(os.path.join(cache_path, 'index.json'))
        old_catalog = load_catalog(self.publication_index_path)
        published_catalog = MapCatalog()
        for map_id in sorted(set([m['map_id'] for m in cached_catalog.maps])):
            cached_list = cached_catalog.find_list_by_id(map_id)
            cached_file_list = [x['file'] for x in cached_list]

            map_info = MapPublication.__create_map_description(cached_list)
            map_file = map_info['file']
            old_map = old_catalog.find_by_file(map_file)

            if not force and old_map is not None and old_map['version'] == map_info['version']:
                self.log.info('Maps [%s] already published as [%s].' % (cached_file_list, map_file))
                published_catalog.add_map(map_info)
                continue

            # noinspection PyBroadException
            try:
                self.__import_maps(cache_path, cached_list, map_info)
                self.log.info('Map(s) [%s] imported as [%s].' % (cached_file_list, map_file))
                published_catalog.add_map(map_info)
            except:
                self.log.error('Map [%s] import skipped due error %s.' % (map_file, sys.exc_info()))

        published_catalog.save(self.publication_index_path)
        published_catalog.save_version(self.publication_version_path)
        published_catalog.save_countries(self.publication_countries_path)

    def __import_maps(self, cache_path, src_map_list, map_info):
        publication_map_path = os.path.join(self.publication_path, map_info['file'])
        temp_root = self.__create_tmp()
        try:
            map_folder = self.__create_tmp(temp_root)
            for src_zip_with_pmz in [os.path.join(cache_path, x['file']) for x in src_map_list]:
                map_folder = self.__extract_pmz(src_zip_with_pmz, temp_root, map_folder)

            convert_map(map_info, map_folder, map_folder + '.converted', self.log)

            zip_folder(map_folder + '.converted', publication_map_path)
            map_info['size'] = os.path.getsize(publication_map_path)

        finally:
            shutil.rmtree(temp_root)

    def __extract_pmz(self, src_zip_with_pmz, temp_folder, map_folder):
        extract_folder = self.__create_tmp(temp_folder)
        unzip_file(src_zip_with_pmz, extract_folder)
        pmz_file = find_file_by_extension(extract_folder, '.pmz')
        unzip_file(pmz_file, map_folder)
        return map_folder

    def __create_tmp(self, folder=None, create=True):
        if folder is None:
            folder = self.temp_path
        tmp_folder = os.path.join(folder, uuid.uuid1().hex)
        if create:
            os.mkdir(tmp_folder)
        return tmp_folder