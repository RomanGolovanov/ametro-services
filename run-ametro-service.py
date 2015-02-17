#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from pmetro.Convertor import convert_vec_to_svg, convert_files_in_folder, UNKNOWN_COMMANDS

from pmetro.MapCatalogImporter import MapCache, MapPublication

base_dir = ''

cache_path = os.path.join(base_dir, 'cache')
publication_path = os.path.join(base_dir, 'www')
temp_path = os.path.join(base_dir, 'tmp')

pmetro_url = 'http://pmetro.chpeks.com/'

#cache = MapCache(pmetro_url, cache_path)
#cache.refresh()

#publication = MapPublication(publication_path, temp_path)
#publication.import_maps(cache_path)

#convert_vec_to_svg('Belorusskaya.vec','Belorusskaya.svg')
#convert_vec_to_svg('Aeroport.vec','Aeroport.svg')
#convert_vec_to_svg('Tretyakovskaya.vec','Tretyakovskaya.svg')
#print 'Unknown commands: %s' % UNKNOWN_COMMANDS

convert_files_in_folder('MoscowMap', 'MoscowMap.converted')
