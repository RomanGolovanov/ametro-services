#!/usr/bin/python
# -*- coding: utf-8 -*-
import codecs
import os


class GeoCity:
    def __init__(self, uid, name, ascii_name, search, latitude, longitude, country_iso):
        self.Uid = uid
        self.Name = name
        self.AsciiName = ascii_name
        self.Search = search
        self.Latitude = latitude
        self.Longitude = longitude
        self.CountryIso = country_iso


class GeoCountry:
    def __init__(self, uid, name, iso, search):
        self.Uid = uid
        self.Name = name
        self.CountryIso = iso
        self.Search = search


class GeoNamesProvider:
    def __init__(self):
        self.citiesByCountry = {}
        self.cities = []
        self.countries = []
        self.__load_cities()
        self.__load_countries()


    def __load_cities(self):
        cities_by_country = {}
        cities = []
        with codecs.open(os.path.join(os.path.dirname(__file__), 'cities.dict'), encoding='utf-8') as f:
            for l in f.readlines():
                p = l.rstrip().split('\t')
                if len(p) <= 8:
                    continue

                iso = p[8].upper()
                if iso in cities_by_country:
                    country_cities = cities_by_country[iso]
                else:
                    country_cities = []
                    cities_by_country[iso] = country_cities

                obj = GeoCity(long(p[0]), p[1], p[2].lower(), p[3].lower(), float(p[4]), float(p[5]), iso)
                country_cities.append(obj)
                cities.append(obj)

        self.citiesByCountry = cities_by_country
        self.cities = cities

    def __load_countries(self):
        countries = []
        with codecs.open(os.path.join(os.path.dirname(__file__), 'countries.dict'), encoding='utf-8') as f:
            for l in f.readlines():
                p = l.rstrip().split(',')
                countries.append(GeoCountry(long(p[0]), p[3], p[1], p[4]))
        self.countries = countries


    def __find_country_by_name(self, name):
        lowercase_name = name.lower()
        for c in self.countries:
            if lowercase_name == c.Search.lower() or lowercase_name == c.Name.lower():
                return c
        return None


    def get_country_name_by_iso(self, iso):
        for c in self.countries:
            if iso == c.CountryIso:
                return c.Name
        return None

    @staticmethod
    def __find_geo_name_country(cities, name):
        lowercase_name = name.lower()
        for c in cities:
            if lowercase_name == c.Name.lower() or lowercase_name == c.AsciiName:
                return c

        for c in cities:
            if lowercase_name in c.Search:
                for p in c.Search.split(','):
                    if lowercase_name == p:
                        return c

        for c in cities:
            if lowercase_name in c.Search:
                return c

        return None


    def find_city(self, name, country_name):

        country = self.__find_country_by_name(country_name)
        if country is not None:
            c = self.__find_geo_name_country(self.citiesByCountry[country.CountryIso], name)
            if c is not None:
                return c

        return self.__find_geo_name_country(self.cities, name)
