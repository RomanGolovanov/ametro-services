import os
import sqlite3


class GeoNamesCity(object):
    def __init__(self, db_record):
        self.geoname_id = db_record[0]
        self.name = db_record[1]
        self.ascii_name = db_record[2]
        self.search = db_record[3]
        self.latitude = db_record[4]
        self.longitude = db_record[5]
        self.country_geoname_id = db_record[6]
        self.country = db_record[7]
        self.iso = db_record[8]


class GeoNamesCountry(object):
    def __init__(self, db_record):
        self.geoname_id = db_record[0]
        self.name = db_record[1]
        self.iso = db_record[2]


class GeoName(object):
    def __init__(self, geoname_id, name):
        self.geoname_id = geoname_id
        self.name = name


class GeoNamesProvider(object):
    def __init__(self):
        self.cnn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'geonames.db'))
        self.cursor = self.cnn.cursor()

    def find_city(self, name, country_name):
        cities = self.__find_cities(name)
        if not any(cities):
            return None

        country = self.find_country(country_name)
        if country is not None:
            city = self.__find_geo_name_in_country([c for c in cities if c.iso == country.iso], name)
            if city is not None:
                return city

        return self.__find_geo_name_in_country(cities, name)

    def find_country(self, name):
        name = name.lower()
        self.cursor.execute('SELECT geoname_id, name, iso FROM country WHERE search_name LIKE ? OR iso LIKE ?',
                            (name, name.upper()))
        result = self.cursor.fetchall()
        if any(result):
            return GeoNamesCountry(result[0])

        self.cursor.execute('SELECT geoname_id, is_pref FROM alt_name WHERE search_name LIKE ?', (name, ))
        items = self.cursor.fetchall()

        for geoname_id in [x[0] for x in items]:
            self.cursor.execute('SELECT geoname_id, name, iso FROM country WHERE geoname_id = ?', (geoname_id,))
            result = self.cursor.fetchall()
            if any(result):
                return GeoNamesCountry(result[0])

        return None

    def get_city_info(self, geoname_id):
        self.cursor.execute('SELECT city.geoname_id, city.name, city.ascii_name, city.search_name, ' +
                            '       city.latitude, city.longitude, country.name, country.iso ' +
                            'FROM city ' +
                            'INNER JOIN country ON country.iso = city.country_iso ' +
                            'WHERE city.geoname_id = ?', (geoname_id,))

        return GeoNamesCity(self.cursor.fetchone())

    def get_cities_info(self, geoname_ids):
        self.cursor.execute('SELECT city.geoname_id, city.name, city.ascii_name, city.search_name, ' +
                            '       city.latitude, city.longitude, country.geoname_id, country.name, country.iso ' +
                            'FROM city ' +
                            'INNER JOIN country ON country.iso = city.country_iso ' +
                            'WHERE city.geoname_id IN ({0})'.format(','.join(map(str, geoname_ids))))

        return [GeoNamesCity(c) for c in self.cursor.fetchall()]

    def get_names_for_language(self, geoname_ids, language_code):
        self.cursor.execute('SELECT geoname_id, name, is_pref FROM alt_name ' +
                            'WHERE geoname_id IN ({0}) AND language = ?'.format(','.join(map(str, geoname_ids))),
                            (language_code,))

        items = self.cursor.fetchall()
        names = dict()
        for geoname_id in geoname_ids:
            preferred_item = [i for i in items if i[0] == geoname_id and i[2] == 1]
            if any(preferred_item):
                names[geoname_id] = preferred_item[0][1]
            else:
                item = [i for i in items if i[0] == geoname_id]
                if any(item):
                    names[geoname_id] = item[0][1]

        return names

    def __find_cities(self, name):
        name = name.lower()
        self.cursor.execute('SELECT city.geoname_id, city.name, city.ascii_name, city.search_name, ' +
                            '       city.latitude, city.longitude, country.name, country.iso ' +
                            'FROM city ' +
                            'INNER JOIN country ON country.iso = city.country_iso ' +
                            'WHERE LOWER(city.search_name) LIKE ?',
                            ('%' + name + '%',))

        return [GeoNamesCity(c) for c in self.cursor.fetchall()]

    @staticmethod
    def __find_geo_name_in_country(cities, name):
        lowercase_name = name.lower()
        for c in cities:
            if lowercase_name == c.name.lower() or lowercase_name == c.ascii_name.lower():
                return c
        for c in cities:
            if lowercase_name in c.search:
                for p in c.search.split(','):
                    if lowercase_name == p:
                        return c
        for c in cities:
            if lowercase_name in c.search:
                return c
        return None

