#!/usr/bin/python
# -*- coding: utf-8 -*-

import codecs
import urllib
import urllib2
import xml.etree.ElementTree as ET
import json
import os


def __load_geo_names():
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


def __load_countries():
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


def __find_geo_name(geo_names, name):
    for c in geo_names:
        if name == c['name'] or name == c['ascii-name']: return c

    for c in geo_names:
        if name in c['search']:
            for p in c['search'].split(','):
                if name == p: return c

    for c in geo_names:
        if name in c['search']: return c

    return None


def __find_country(countries, iso):
    for c in countries:
        if iso == c['iso']: return c
    return None


def __download_map_index(service_url):
    geo_names = __load_geo_names()
    countries = __load_countries()

    xml_maps = urllib.urlopen(service_url + 'Files.xml').read().decode('windows-1251').encode('utf-8')
    maps = []
    max_version = 0
    for el in ET.fromstring(xml_maps):
        if el.find('City').attrib['Country'] == u' Программа' or el.find('City').attrib['CityName'] == u'':
            continue

        geo_name = __find_geo_name(geo_names, el.find('City').attrib['CityName'])

        if geo_name is None:
            continue

        version = int(el.find('Zip').attrib['Date'])
        if version > max_version: max_version = version

        #print geo_name['name'], geo_name['iso']

        maps.append({
            'id': geo_name['id'],
            'city': geo_name['name'],
            'iso': geo_name['iso'],
            'country': __find_country(countries, geo_name['iso'])['en'],
            'latitude': geo_name['latitude'],
            'longitude': geo_name['longitude'],
            'file': el.find('Zip').attrib['Name'],
            'version': version,
            'size': int(el.find('Zip').attrib['Size'])
        })
    return {'version': max_version, 'maps': maps}


def __download_map(service_url, folder, map):
    req = urllib2.urlopen(service_url + map['file'])
    chunk_size = 16 * 1024
    with open(os.path.join(folder, map['file'] + ".download"), 'wb') as fp:
        while True:
            chunk = req.read(chunk_size)
            if not chunk: break
            fp.write(chunk)
    os.rename(os.path.join(folder, map['file'] + ".download"), os.path.join(folder, map['file']))
    #print map['file'] + ' downloaded'


def __find_map_by_file(maps, file_name):
    for m in maps['maps']:
        if m['file'] == file_name:
            return m
    return None


def __store_map_index_version(map_index, path):
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(
            json.dumps({'version': map_index['version']}, ensure_ascii=False, indent=True))


def __store_map_index_country_iso_codes(maps, path):
    country_iso_dict = {}

    for m in maps['maps']:
        country_name = m['country']
        country_iso = m['iso']
        country_iso_dict[country_name] = country_iso

    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(
            json.dumps(country_iso_dict, ensure_ascii=False, indent=True))


def store_map_index(map_index, path):
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(
            json.dumps(map_index, ensure_ascii=False, indent=True))


def load_map_index(path):
    with codecs.open(path, 'r', 'utf-8') as f:
        return json.load(f)


def update_maps_cache(service_url, working_path):
    if not os.path.isdir(working_path):
        os.mkdir(working_path)

    maps_new = __download_map_index(service_url)
    maps_index_path = os.path.join(working_path, "index.json")

    try:
        maps_old = load_map_index(maps_index_path)
    except IOError:
        maps_old = None

    if maps_old is None:
        for m in maps_new['maps']:
            __download_map(service_url, working_path, m)
        return
    else:
        for m in maps_new['maps']:
            o = __find_map_by_file(maps_old, m['file'])
            if o is None or o['version'] < m['version'] or o['size'] <> m['size']:
                __download_map(service_url, working_path, m)

    __store_map_index_version(maps_new, os.path.join(working_path, "version.json"))
    __store_map_index_country_iso_codes(maps_new, os.path.join(working_path, "iso.json"))
    store_map_index(maps_new, maps_index_path)
    return None
