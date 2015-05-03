import os
import shutil
import uuid
import sys

from pmetro.file_utils import unzip_file, zip_folder, find_file_by_extension
from pmetro.log import EmptyLog
from pmetro.pmz_import import convert_map
from publishing.catalog import load_catalog, MapCatalog


class MapImporter(object):
    def __init__(self, import_path, temp_path, log, geoname_provider):
        self.__log = log
        self.__import_path = import_path
        self.__index_path = os.path.join(import_path, 'index.json')
        self.__timestamp_path = os.path.join(import_path, 'timestamp.json')
        self.__countries_path = os.path.join(import_path, 'countries.json')
        self.__temp_path = temp_path
        self.__geoname_provider = geoname_provider

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

            convert_map(map_info['city_id'], map_info['file'], map_info['timestamp'], map_folder, converted_folder,
                        self.__log, self.__geoname_provider)

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

