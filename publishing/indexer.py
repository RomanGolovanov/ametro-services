import os
import shutil
import uuid
import zipfile
from datetime import date, datetime, timedelta
from os import listdir
from os.path import isfile, join

from pmetro.file_utils import unzip_file, find_file_by_extension
from pmetro.ini_files import deserialize_ini, get_ini_attr


class MapIndexer(object):
    def __init__(self, working_path, index_path, temp_path, logger):
        self.__working_path = working_path
        self.__index_path = index_path
        self.__temp_path = temp_path
        self.__logger = logger

    def make_index(self):

        if not os.path.exists(self.__index_path):
            os.makedirs(self.__index_path)

        pmz_files = [f for f in listdir(self.__working_path) if (isfile(join(self.__working_path, f)) and f.endswith('pmz'))]
        self.__logger.debug('Found %s files' % (len(pmz_files)))

        index = []

        for pmz_file in pmz_files:
            self.__logger.info('extract metadata from %s' % pmz_file)
            zip_file = pmz_file.replace('.pmz', '.zip')
            pmz_file_path = join(self.__working_path, pmz_file)
            zip_file_path = join(self.__index_path, zip_file)

            self.__pack_pmz(pmz_file_path, zip_file_path, pmz_file)
            map_item = {
                'ZipName': zip_file,
                'ZipSize': os.path.getsize(zip_file_path),
                'PmzName': pmz_file,
                'PmzSize': os.path.getsize(pmz_file_path),
                'Date': (date.fromtimestamp(os.path.getmtime(pmz_file_path)) - date(1899, 12, 30)).days,
                'Name': '',
                'CityName': '',
                'Country': ''
            }
            self.__fill_map_info(map_item, pmz_file_path)
            index.append(map_item)

        xml = ''
        xml += '<?xml version="1.0" encoding="windows-1251"?>\n'
        xml += '<FileList DataVersion="1" Date="43102">\n'
        for i in index:
            xml += '  <File>\n'
            xml += ('    <Zip Name="%s" Size="%s" Date="%s"/>\n' % (i['ZipName'], i['ZipSize'], i['Date']))
            xml += ('    <Pmz Name="%s" Size="%s" Date="%s"/>\n' % (i['PmzName'], i['PmzSize'], i['Date']))
            xml += ('    <City Name="%s" CityName="%s" Country="%s"/>\n' % (i['Name'], i['CityName'], i['Country']))
            xml += '  </File>\n'

        xml += '</FileList>\n'

        with open(join(self.__index_path, 'Files.xml'), 'wb') as xml_file:
            xml_file.write(xml.encode('windows-1251'))

    def __fill_map_info(self, map_item, pmz_file_path):
        temp_folder = os.path.join(self.__temp_path, uuid.uuid1().hex)
        try:
            unzip_file(pmz_file_path, temp_folder)
            ini = deserialize_ini(find_file_by_extension(temp_folder, '.cty'))['Options']
            map_item['Name'] = ini['Name']
            map_item['CityName'] = ini['CityName']
            map_item['Country'] = ini['Country']
        finally:
            shutil.rmtree(temp_folder)

    @staticmethod
    def __pack_pmz(pmz_file, zip_file, pmz_file_name):
        if isfile(zip_file):
            os.remove(zip_file)

        zf = zipfile.ZipFile(zip_file, mode='w')
        try:
            zf.write(pmz_file, pmz_file_name)
        finally:
            zf.close()
