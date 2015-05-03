import zipfile
import codecs
import json
import os
import shutil

from globalization.settings import LANGUAGE_SET
from pmetro.file_utils import get_file_ext
from pmetro.serialization import write_as_json_file


class MapIndexEntity(object):
    def __init__(self, uid, city_id, file, size, timestamp, transports, latitude, longitude):
        self.uid = uid
        self.city_id = city_id
        self.file = file
        self.size = size
        self.timestamp = timestamp
        self.transports = transports
        self.latitude = latitude
        self.longitude = longitude


def publish_maps(maps_path, publishing_path, geonames_provider):
    __publish_maps(maps_path, publishing_path)
    __rebuild_cities_index(publishing_path, geonames_provider)


def __publish_maps(maps_path, publishing_path):
    for file_name in [f for f in os.listdir(maps_path) if get_file_ext(os.path.join(maps_path, f)) == 'zip']:
        source_file = os.path.join(maps_path, file_name)
        destination_file = os.path.join(publishing_path, file_name)

        if os.path.isfile(destination_file) and os.path.getsize(source_file) == os.path.getsize(
                destination_file) and os.path.getmtime(source_file) == os.path.getmtime(destination_file):
            continue

        if os.path.isfile(destination_file):
            os.remove(destination_file)
        shutil.copy2(source_file, publishing_path)


def __rebuild_cities_index(publishing_path, geonames_provider):
    locales_path = os.path.join(publishing_path, 'locales')
    if not os.path.isdir(locales_path):
        os.mkdir(locales_path)

    maps_index = sorted(__create_index(publishing_path), key=lambda k: k.uid)
    write_as_json_file(maps_index, os.path.join(publishing_path, 'index.json'))
    write_as_json_file(dict(timestamp=max(maps_index, key=lambda x: x.timestamp).timestamp),
                       os.path.join(publishing_path, 'timestamp.json'))

    localizations = __create_localized_cities_list(geonames_provider, (m.city_id for m in maps_index))

    for locale in localizations['locales']:
        write_as_json_file(localizations['locales'][locale],
                           os.path.join(locales_path, 'cities.{0}.json'.format(locale)))

    write_as_json_file(localizations['locales'][localizations['default_locale']],
                       os.path.join(locales_path, 'cities.default.json'))


def __create_localized_cities_list(geonames_provider, city_ids, show_defaults=False):
    cities = geonames_provider.get_cities_info(city_ids)

    all_ids = set([c.geoname_id for c in cities] + [c.country_geoname_id for c in cities])

    locales = dict()
    for language_code in LANGUAGE_SET:
        names = geonames_provider.get_names_for_language(all_ids, language_code)
        locale = []
        for city_info in cities:

            defaults = []
            if city_info.geoname_id in names:
                city_name = names[city_info.geoname_id]
            else:
                city_name = city_info.name
                defaults.append('city')

            if city_info.country_geoname_id in names:
                country_name = names[city_info.country_geoname_id]
            else:
                country_name = city_info.country
                defaults.append('country')

            if show_defaults:
                locale_entity = (
                    city_info.geoname_id,
                    city_name,
                    country_name,
                    city_info.iso,
                    ','.join(defaults) if any(defaults) else None)
            else:
                locale_entity = (
                    city_info.geoname_id,
                    city_name,
                    country_name,
                    city_info.iso)

            locale.append(locale_entity)

        locales[language_code] = locale

    return dict(locales=locales, default_locale='en')


def __create_index(maps_path):
    for map_file in [f for f in os.listdir(maps_path) if get_file_ext(os.path.join(maps_path, f)) == 'zip']:
        full_map_file_path = os.path.join(maps_path, map_file)
        meta = __get_map_metadata(full_map_file_path)
        yield MapIndexEntity(
            meta['map_id'],
            meta['city_id'],
            map_file,
            os.path.getsize(full_map_file_path),
            meta['timestamp'],
            sorted([transport['type'] for transport in meta['transports']]),
            meta['latitude'],
            meta['longitude']
        )


def __get_map_metadata(map_path):
    with zipfile.ZipFile(map_path, 'r') as zip_file:
        index_json = codecs.decode(zip_file.read('index.json'), 'utf-8)')
        return json.loads(index_json)


