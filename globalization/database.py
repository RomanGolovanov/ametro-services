import codecs
import os
import sqlite3
import zipfile

__CREATE_CITY_TABLE_QUERY = 'CREATE TABLE city (' + \
                            'geoname_id int, name text, ascii_name text, search_name text, latitude real, ' + \
                            'longitude real, country_iso text)'
__INSERT_CITY_TABLE_QUERY = 'INSERT INTO city VALUES (?,?,?,?,?,?,?)'

__CREATE_COUNTRY_TABLE_QUERY = 'CREATE TABLE country (geoname_id int, iso text, name text, capital text)'
__INSERT_COUNTRY_TABLE_QUERY = 'INSERT INTO country VALUES (?,?,?,?)'

__MAX_BATCH_SIZE = 10000

__CITIES_GEO_NAME_FILE = 'cities1000.zip'
__COUNTRIES_GEO_NAME_FILE = 'countryInfo.zip'


def create_geonames_database(src_path, dst_path, force=False):
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
    cursor = cnn.cursor()
    cursor.execute(__CREATE_CITY_TABLE_QUERY)
    cnn.commit()
    cursor.execute(__CREATE_COUNTRY_TABLE_QUERY)
    cnn.commit()
    __fill_table(cnn, cursor, src_path, __COUNTRIES_GEO_NAME_FILE, __parse_country_record, __INSERT_COUNTRY_TABLE_QUERY)
    __fill_table(cnn, cursor, src_path, __CITIES_GEO_NAME_FILE, __parse_city_record, __INSERT_CITY_TABLE_QUERY)


def __fill_table(cnn, cursor, src_path, src_name, parse_func, insert_query):
    src_full_name = os.path.join(src_path, src_name)
    if src_name.endswith('.zip'):
        with zipfile.ZipFile(src_full_name, 'r') as zip:
            for zip_entry_name in zip.namelist():
                with zip.open(zip_entry_name, 'r') as f:
                    __process_lines(codecs.iterdecode(f, encoding='utf-8'), cnn, cursor, insert_query, parse_func,
                                    src_name)
    else:
        with codecs.open(src_full_name, 'r', encoding='utf-8') as f:
            __process_lines(f, cnn, cursor, insert_query, parse_func, src_name)


def __process_lines(lines, cnn, cursor, insert_query, parse_func, source_file):
    batch = []
    record_count = 0
    for line in lines:
        if line is None or len(line) == 0 or line[0] == '#':
            continue

        batch.append(parse_func(line))
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
    print('complete importing data from [%s], processed %s records' % (source_file, record_count))


def __parse_city_record(text):
    geoname_id, name, ascii_name, alternate_names, latitude, longitude, feature_class, feature_code, country_code, \
    cc2, admin1_code, admin2_code, admin3_code, admin4_code, population, elevation, dem, timezone, modification_date \
        = str(text).split('\t')
    return geoname_id, name, ascii_name, alternate_names, latitude, longitude, country_code


def __parse_country_record(text):
    iso, iso3, iso_numeric, fips, name, capital, area_sq_km, population, continent, \
    tld, currency_code, currency_name, phone, postal_code_format, postal_code_regex, \
    languages, geo_name_id, neighbours, equivalent_fips \
        = str(text).split('\t')
    return geo_name_id, iso, name, capital

