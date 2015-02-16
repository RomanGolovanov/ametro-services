# -*- coding: utf-8 -*-
import codecs
import json
import os
import shutil
import string
import urllib
import urllib2
import uuid
import sys
from globalization.GeoNames import GeoNamesProvider
import xml.etree.ElementTree as ET
from pmetro.FileUtils import unzip_file, zip_folder, find_file_by_extension
from pmetro.IniReader import IniReader


class MapCatalog(object):
    def __init__(self, maps=None):
        if not maps:
            maps = []
        self.maps = maps

    def add(self, uid, city, country, iso, latitude, longitude, file, size, version):
        self.maps.append({
            'id': uid,
            'city': city,
            'iso': iso,
            'country': country,
            'latitude': latitude,
            'longitude': longitude,
            'file': file,
            'size': size,
            'version': version
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

    @staticmethod
    def clone(source_map):
        cloned_map = {
            'id': source_map['id'],
            'city': source_map['city'],
            'iso': source_map['iso'],
            'country': source_map['country'],
            'latitude': source_map['latitude'],
            'longitude': source_map['longitude'],
            'file': source_map['file'],
            'size': source_map['size'],
            'version': source_map['version']
        }
        return cloned_map

    def add_map(self, map_info):
        self.maps.append(map_info)


class MapCache(object):
    def __init__(self, service_url, cache_path):
        self.download_chunk_size = 16 * 1024
        self.service_url = service_url
        self.cache_path = cache_path
        self.cache_index_path = os.path.join(cache_path, 'index.json')

        if not os.path.isdir(cache_path):
            os.mkdir(cache_path)

    def refresh(self):

        new_catalog = self.__download_map_index()

        old_catalog = MapCatalog()

        # noinspection PyBroadException
        try:
            old_catalog.load(self.cache_index_path)
        except:
            old_catalog = None

        if old_catalog is None:
            for new_map in new_catalog.maps:
                self.__download_map(new_map)
        else:
            for new_map in new_catalog.maps:
                old_map = old_catalog.find_by_file(new_map['file'])
                if old_map is None or old_map['version'] < new_map['version'] or old_map['size'] != new_map['size']:
                    self.__download_map(new_map)

            for old_map in old_catalog.maps:
                new_map = new_catalog.find_by_file(old_map['file'])
                if new_map is None:
                    os.remove(os.path.join(self.cache_path, new_map['file']))

        new_catalog.save(self.cache_index_path)

    def __download_map_index(self):
        geonames_provider = GeoNamesProvider()

        xml_maps = urllib.urlopen(self.service_url + 'Files.xml').read().decode('windows-1251').encode('utf-8')

        catalog = MapCatalog()
        for el in ET.fromstring(xml_maps):
            city_name = el.find('City').attrib['CityName']
            country_name = el.find('City').attrib['Country']
            file_name = el.find('Zip').attrib['Name']
            size = int(el.find('Zip').attrib['Size'])
            version = int(el.find('Zip').attrib['Date'])

            if country_name == u' Программа' or city_name == u'':
                print 'Skipped %s, [%s]/[%s]' % (file_name, city_name, country_name)
                continue

            city = geonames_provider.find_city(city_name, country_name)
            if city is None:
                print 'Not found %s, [%s]/[%s]' % (file_name, city_name, country_name)
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
        temp_file_path = os.path.join(self.cache_path, map_item['file'] + '.download')
        map_file_path = os.path.join(self.cache_path, map_item['file'])

        req = urllib2.urlopen(self.service_url + map_item['file'])
        with open(temp_file_path, 'wb') as fp:
            while True:
                chunk = req.read(self.download_chunk_size)
                if not chunk:
                    break
                fp.write(chunk)

        if os.path.isfile(map_file_path):
            os.remove(map_file_path)

        os.rename(temp_file_path, map_file_path)
        print 'Downloaded [%s]' % (map_item['file'])


class MapPublication(object):
    def __init__(self, publication_path, temp_path):

        self.temp_path = temp_path
        if not os.path.isdir(temp_path):
            os.mkdir(temp_path)

        self.publication_path = publication_path
        self.publication_index_path = os.path.join(publication_path, 'index.json')
        self.publication_version_path = os.path.join(publication_path, 'version.json')
        self.publication_countries_path = os.path.join(publication_path, 'countries.json')
        if not os.path.isdir(publication_path):
            os.mkdir(publication_path)

    def import_maps(self, cache_path):

        cached_catalog = MapCatalog()
        cached_catalog.load(os.path.join(cache_path, 'index.json'))

        old_catalog = MapCatalog()

        # noinspection PyBroadException
        try:
            old_catalog.load(self.publication_index_path)
        except:
            old_catalog = MapCatalog()

        published_catalog = MapCatalog()
        for cached_map in cached_catalog.maps:
            map_info = published_catalog.clone(cached_map)
            map_file = map_info['file']

            old_map = old_catalog.find_by_file(map_file)
            if old_map is not None and old_map['version'] == map_info['version']:
                published_catalog.add_map(old_map)
                continue

            self.__import_map(cache_path, map_file, map_info)
            published_catalog.add_map(map_info)
            print 'Map [%s] imported.' % map_file

        published_catalog.save(self.publication_index_path)
        published_catalog.save_version(self.publication_version_path)
        published_catalog.save_countries(self.publication_countries_path)

    def __import_map(self, cache_path, map_file, map_info):
        publication_map_path = os.path.join(self.publication_path, map_file)
        temp_folder = os.path.join(self.temp_path, uuid.uuid1().hex)
        try:
            unzip_file(os.path.join(cache_path, map_file), temp_folder)

            pmz_file = find_file_by_extension(temp_folder, '.pmz')
            map_folder = pmz_file[0:-4]
            unzip_file(pmz_file, map_folder)

            self.__fill_map_info(map_folder, map_info)
            self.__convert_assets()

            zip_folder(map_folder, publication_map_path)
            map_info['size'] = os.path.getsize(publication_map_path)

        except:
            print "Unexpected error:", sys.exc_info()
            raise
        finally:
            shutil.rmtree(temp_folder)

    @staticmethod
    def __fill_map_info(map_folder, map_info):
        reader = IniReader()
        reader.open(find_file_by_extension(map_folder, '.cty'), 'windows-1251')
        reader.section(u'Options')

        comments = []
        description = []
        while reader.read():
            if reader.name() == 'comment':
                comments.append(reader.value().replace('\\n', '\n').rstrip())
            if reader.name() == 'mapauthors':
                description.append(reader.value().replace('\\n', '\n').rstrip())

        if any(comments):
            map_info['comments'] = string.join(comments, '\n').rstrip('\n')

        if any(description):
            map_info['description'] = string.join(description, '\n').rstrip('\n')

    def __convert_assets(self):
        pass













