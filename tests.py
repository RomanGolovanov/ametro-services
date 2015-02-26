import os
import sqlite3
from globalization.builder import build_geonames_database

#build_geonames_database('c:/temp/geonames', force = True)

cnn = sqlite3.connect('geonames/geonames.db')
cursor = cnn.cursor()
cursor.execute('SELECT * FROM alt_name')
items = cursor.fetchall()

y = [x for x in items if x[0] == 524901]

print(y)