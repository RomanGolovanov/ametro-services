import codecs
import os
import sqlite3
import zipfile

__CREATE_CITY_TABLE_QUERY = 'CREATE TABLE city (' + \
                            '   geoname_id int, name text, ascii_name text, search_name text, latitude real, ' + \
                            '   longitude real, country_iso text, population int)'
__CREATE_CITY_INDEX_QUERY = 'CREATE INDEX IX_alt_name_search ON alt_name (search_name)'
__INSERT_CITY_TABLE_QUERY = 'INSERT INTO city VALUES (?,?,?,?,?,?,?,?)'

__CREATE_COUNTRY_TABLE_QUERY = 'CREATE TABLE country (' + \
                               '    geoname_id int, iso text, name text, capital text, search_name text)'
__CREATE_COUNTRY_INDEX_QUERY = 'CREATE INDEX IX_county_search ON country (search_name)'
__INSERT_COUNTRY_TABLE_QUERY = 'INSERT INTO country VALUES (?,?,?,?,?)'

__CREATE_ALT_NAME_TABLE_QUERY = 'CREATE TABLE alt_name (geoname_id int, language text, name text, search_name text)'
__CREATE_ALT_NAME_INDEX_QUERY = 'CREATE INDEX IX_city_search ON country (search_name)'
__INSERT_ALT_NAME_TABLE_QUERY = 'INSERT INTO alt_name VALUES (?,?,?,?)'

__MAX_BATCH_SIZE = 10000

__CITIES_GEO_NAME_FILE = 'cities1000.zip'
__COUNTRIES_GEO_NAME_FILE = 'countryInfo.zip'
__ALT_GEO_NAME_FILE = 'alternateNames.zip'

__ALT_LANGUAGE_SET = {'en', 'ru', 'es', 'it', 'fr', 'ja', 'fi', 'pl', 'de'}


def build_geonames_database(geonames_path, force=False):
    dst_path = os.path.dirname(__file__)
    database_path = os.path.join(dst_path, 'geonames.db')
    if os.path.isfile(database_path):
        if not force:
            return
        else:
            os.remove(database_path)

    if not os.path.isdir(dst_path):
        os.mkdir(dst_path)

    print('Create GeoNames database')
    cnn = sqlite3.connect(database_path)
    c = cnn.cursor()
    c.execute(__CREATE_CITY_TABLE_QUERY)
    c.execute(__CREATE_COUNTRY_TABLE_QUERY)
    c.execute(__CREATE_ALT_NAME_TABLE_QUERY)
    cnn.commit()
    __fill_table(cnn, c, geonames_path, __COUNTRIES_GEO_NAME_FILE, __parse_country_record, None,
                 __INSERT_COUNTRY_TABLE_QUERY)
    __fill_table(cnn, c, geonames_path, __CITIES_GEO_NAME_FILE, __parse_city_record, None, __INSERT_CITY_TABLE_QUERY)

    c.execute('SELECT geoname_id FROM city')
    city_ids = [x[0] for x in c.fetchall()]
    c.execute('SELECT geoname_id FROM country')
    country_ids = [x[0] for x in c.fetchall()]

    __fill_table(cnn, c, geonames_path, __ALT_GEO_NAME_FILE, __parse_alt_name, set(city_ids + country_ids),
                 __INSERT_ALT_NAME_TABLE_QUERY)

    c.execute(__CREATE_CITY_INDEX_QUERY)
    c.execute(__CREATE_COUNTRY_INDEX_QUERY)
    c.execute(__CREATE_ALT_NAME_INDEX_QUERY)
    cnn.commit()


def __fill_table(cnn, cursor, src_path, src_name, parse_func, parse_context, insert_query):
    src_full_name = os.path.join(src_path, src_name)
    with zipfile.ZipFile(src_full_name, 'r') as zf:
        for zip_entry_name in zf.namelist():
            if zip_entry_name[:-3] != src_name[:-3]:
                continue
            with zf.open(zip_entry_name, 'r') as f:
                __process_lines(codecs.iterdecode(f, encoding='utf-8'), cnn, cursor, insert_query,
                                parse_func, parse_context, src_name)


def __process_lines(lines, cnn, cursor, insert_query, parse_func, parse_context, source_file):
    batch = []
    record_count = 0
    for line in lines:
        if line is None or len(line) == 0 or line[0] == '#':
            continue

        value = parse_func(line, parse_context)
        if value is None:
            continue

        batch.append(value)
        record_count += 1
        if len(batch) >= __MAX_BATCH_SIZE:
            print('inserting batch of %s records' % len(batch))
            cursor.executemany(insert_query, batch)
            batch = []
            cnn.commit()
    if len(batch) >= 1:
        print('inserting final batch of %s records' % len(batch))
        cursor.executemany(insert_query, batch)
        cnn.commit()
    print('complete importing data from %s, processed %s records' % (source_file, record_count))


def __parse_city_record(text, context):
    geoname_id, name, ascii_name, alternate_names, latitude, longitude, feature_class, feature_code, country_code, \
    cc2, admin1_code, admin2_code, admin3_code, admin4_code, population, elevation, dem, timezone, modification_date \
        = str(text).split('\t')

    search = [name.lower(), ascii_name.lower(), alternate_names.lower()]

    return geoname_id, name, ascii_name, \
           ','.join(search), \
           latitude, longitude, country_code, population


def __parse_country_record(text, context):
    iso, iso3, iso_numeric, fips, name, capital, area_sq_km, population, continent, \
    tld, currency_code, currency_name, phone, postal_code_format, postal_code_regex, \
    languages, geo_name_id, neighbours, equivalent_fips \
        = str(text).split('\t')
    return geo_name_id, iso, name, capital, name.lower()


def __parse_alt_name(text, context):
    alt_name_id, geoname_id, language, name, is_pref, is_short, is_colloquial, is_historic = str(text).split('\t')
    if is_colloquial == '1' or is_historic == '1':
        return None
    if language not in __ALT_LANGUAGE_SET:
        return None
    if int(geoname_id) not in context:
        return None
    return geoname_id, language, name, name.lower()
