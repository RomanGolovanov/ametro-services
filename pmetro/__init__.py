#!/usr/bin/python
# -*- coding: utf-8 -*-

import codecs
import urllib
import urllib2
import xml.etree.ElementTree as ET
import json
import time
import os
import zipfile


def download_map_index(service_url):
    xml_maps = urllib.urlopen(service_url + '/Files.xml').read().decode('windows-1251').encode('utf-8')
    print ET.fromstring(xml_maps)
    maps = []
    for el in ET.fromstring(xml_maps):
        country_name = el.find('City').attrib['Country']
        city_name = el.find('City').attrib['CityName']

        if country_name == u' Программа' or city_name == u'':
            continue

        maps.append({
            'city': city_name,
            'country': country_name,
            'file': el.find('Zip').attrib['Name'],
            'url': service_url + '/' + el.find('Zip').attrib['Name'],
            'date': int(el.find('Zip').attrib['Date']),
            'size': int(el.find('Zip').attrib['Size'])
        })
    return {'version': '1.0', 'date': time.time(), 'maps': maps}


def store_map_index(map_index, path):
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(
            json.dumps(map_index, ensure_ascii=False, indent=True))


def download_map_index_files(maps, folder):
    for m in maps['maps']:
        req = urllib2.urlopen(m['url'])
        chunk_size = 16 * 1024
        with open(os.path.join(folder, m['file']), 'wb') as fp:
            while True:
                chunk = req.read(chunk_size)
                if not chunk: break
                fp.write(chunk)
        print m['file'] + ' downloaded'


def pack_file(filename, name, archive):
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip:
        zip.write(filename, name)


