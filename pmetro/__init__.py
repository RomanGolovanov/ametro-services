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


def load_csv_lines(name):
    cities = []
    full_path = os.path.join(os.path.dirname(__file__), name)
    with codecs.open(full_path, encoding='utf-8') as f:
        return f.readlines()


def load_cities():
    cities = []
    for l in load_csv_lines('cities.dict'):
        parts = l.rstrip().split(',')
        cities.append({
            'id': parts[0],
            'country': parts[1],
            'latitude': parts[2],
            'longitude': parts[3],
            'height': parts[4],
            'width': parts[5],
            'en': parts[6],
            'ru': parts[7]
        })
    return cities


def load_countries():
    countries = []
    for l in load_csv_lines('countries.dict'):
        parts = l.rstrip().split(',')
        countries.append({
            'id': parts[0],
            'iso': parts[1],
            'abr': parts[2],
            'en': parts[3],
            'ru': parts[4]
        })
    return countries


def find_city(cities, name):
    for c in cities:
        if c['en'] == name or c['ru'] == name:
            return c
    return None


def find_country(countries, name):
    for c in countries:
        if c['en'] == name or c['ru'] == name:
            return c
    return None


def find_country_by_id(countries, id):
    for c in countries:
        if c['id'] == id:
            return c
    return None


def download_map_index(service_url):

    cities = load_cities()
    countries = load_countries()

    xml_maps = urllib.urlopen(service_url + 'Files.xml').read().decode('windows-1251').encode('utf-8')
    maps = []
    for el in ET.fromstring(xml_maps):
        if el.find('City').attrib['Country'] == u' Программа' or el.find('City').attrib['CityName'] == u'':
            continue

        country_name = find_country(countries, el.find('City').attrib['Country'])
        city_name = find_city(cities, el.find('City').attrib['CityName'])

        if country_name is None or city_name is None:
            print el.find('City').attrib['CityName']
            continue

        maps.append({
            'city': city_name['en'],
            'country': country_name['en'],
            'url': el.find('Zip').attrib['Name'],
            'date': int(el.find('Zip').attrib['Date']),
            'size': int(el.find('Zip').attrib['Size'])
        })
    return {'version': 1, 'date': time.time(), 'maps': maps}


def store_map_index(map_index, path):
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(
            json.dumps(map_index, ensure_ascii=False, indent=True))


def download_map_index_files(maps, service_url, folder):
    for m in maps['maps']:
        req = urllib2.urlopen(service_url + m['url'])
        chunk_size = 16 * 1024
        with open(os.path.join(folder, m['url']), 'wb') as fp:
            while True:
                chunk = req.read(chunk_size)
                if not chunk: break
                fp.write(chunk)
        print m['url'] + ' downloaded'
        return


def pack_file(filename, name, archive):
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip:
        zip.write(filename, name)


