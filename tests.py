import time

from globalization.builder import build_geonames_database
from globalization.provider import GeoNamesProvider


build_geonames_database('c:/temp/geonames', force=False)
from pmetro.model_serialization import as_json



p = GeoNamesProvider()

t1 = time.clock()
r = p.find_city('Алматы','')
t2 = time.clock()

print(t2 - t1)
print(as_json(r))


t1 = time.clock()
r = p.find_city('Алматы','')
t2 = time.clock()

print(t2 - t1)
print(as_json(r))



t1 = time.clock()
r = p.find_city('Алматы','')
t2 = time.clock()

print(t2 - t1)
print(as_json(r))