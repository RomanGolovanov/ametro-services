import codecs
import os


def parse_geoname_record(text):
    # geonameid         : integer id of record in geonames database
    # name              : name of geographical point (utf8) varchar(200)
    # asciiname         : name of geographical point in plain ascii characters, varchar(200)
    # alternatenames    : alternatenames, comma separated, ascii names automatically transliterated, convenience attribute from alternatename table, varchar(10000)
    # latitude          : latitude in decimal degrees (wgs84)
    # longitude         : longitude in decimal degrees (wgs84)
    # feature class     : see http://www.geonames.org/export/codes.html, char(1)
    # feature code      : see http://www.geonames.org/export/codes.html, varchar(10)
    # country code      : ISO-3166 2-letter country code, 2 characters
    # cc2               : alternate country codes, comma separated, ISO-3166 2-letter country code, 60 characters
    # admin1 code       : fipscode (subject to change to iso code), see exceptions below, see file admin1Codes.txt for display names of this code; varchar(20)
    # admin2 code       : code for the second administrative division, a county in the US, see file admin2Codes.txt; varchar(80)
    # admin3 code       : code for third level administrative division, varchar(20)
    # admin4 code       : code for fourth level administrative division, varchar(20)
    # population        : bigint (8 byte int)
    # elevation         : in meters, integer
    # dem               : digital elevation model, srtm3 or gtopo30, average elevation of 3''x3'' (ca 90mx90m) or 30''x30'' (ca 900mx900m) area in meters, integer. srtm processed by cgiar/ciat.
    # timezone          : the timezone id (see file timeZone.txt) varchar(40)
    # modification date : date of last modification in yyyy-MM-dd format

    name_id, name, ascii_name, alternate_names, latitude, longitude, feature_class, feature_code, country_code, cc2, \
    admin1_code, admin2_code, admin3_code, admin4_code, population, elevation, dem, timezone, modification_date \
        = str(text).split('\t')

    return name_id, name, ascii_name, alternate_names, latitude, longitude, country_code


def convert_geo_names_to_sqlite():
    cities_path = os.path.join(os.path.dirname(__file__), 'cities.dict')
    with codecs.open(cities_path, 'r', encoding='utf-8') as cities_file:
        for line in cities_file:
            city_record = parse_geoname_record(line)
            print(city_record)
            break
