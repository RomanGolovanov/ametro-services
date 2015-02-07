#!/usr/bin/python
# -*- coding: utf-8 -*-

import codecs
import urllib
import urllib2
import xml.etree.ElementTree as ET
import json
import os
import zipfile


def load_geo_names():
    names = []
    with codecs.open(os.path.join(os.path.dirname(__file__), 'cities.dict'), encoding='utf-8') as f:
        for l in f.readlines():
            parts = l.rstrip().split('\t')
            if len(parts) <= 8: continue
            names.append({
                'id': parts[0],
                'name': parts[1],
                'ascii-name': parts[2],
                'search': parts[3],
                'latitude': parts[4],
                'longitude': parts[5],
                'iso': parts[8]
            })
    return names


def load_countries():
    countries = []
    with codecs.open(os.path.join(os.path.dirname(__file__), 'countries.dict'), encoding='utf-8') as f:
        for l in f.readlines():
            parts = l.rstrip().split(',')
            countries.append({
                'id': parts[0],
                'iso': parts[1],
                'abr': parts[2],
                'en': parts[3],
                'ru': parts[4]
            })
    return countries


def find_geo_name(geo_names, name):
    for c in geo_names:
        if name == c['name'] or name == c['ascii-name']: return c

    for c in geo_names:
        if name in c['search']:
            for p in c['search'].split(','):
                if name == p: return c

    for c in geo_names:
        if name in c['search']: return c

    return None


def find_country(countries, iso):
    for c in countries:
        if iso == c['iso']: return c
    return None


def download_map_index(service_url):
    geo_names = load_geo_names()
    countries = load_countries()

    xml_maps = urllib.urlopen(service_url + 'Files.xml').read().decode('windows-1251').encode('utf-8')
    maps = []
    max_version = 0
    for el in ET.fromstring(xml_maps):
        if el.find('City').attrib['Country'] == u' Программа' or el.find('City').attrib['CityName'] == u'':
            continue

        geo_name = find_geo_name(geo_names, el.find('City').attrib['CityName'])

        if geo_name is None:
            continue

        version = int(el.find('Zip').attrib['Date'])
        if version > max_version: max_version = version

        print geo_name['name'], geo_name['iso']

        maps.append({
            'id': geo_name['id'],
            'city': geo_name['name'],
            'iso': geo_name['iso'],
            'country': find_country(countries, geo_name['iso'])['en'],
            'latitude': geo_name['latitude'],
            'longitude': geo_name['longitude'],
            'file': el.find('Zip').attrib['Name'],
            'version': version,
            'size': int(el.find('Zip').attrib['Size'])
        })
    return {'version': max_version, 'maps': maps}


def store_map_index(map_index, path):
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(
            json.dumps(map_index, ensure_ascii=False, indent=True))


def download_maps(maps, service_url, folder):
    for m in maps['maps']:
        req = urllib2.urlopen(service_url + m['file'])
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


