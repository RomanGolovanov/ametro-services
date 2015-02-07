#!/usr/bin/python
# -*- coding: utf-8 -*-

import pmetro
import os

working_folder = 'maps'
if not os.path.isdir(working_folder):
    os.mkdir(working_folder)

pmetro_url = 'http://pmetro.chpeks.com/'

maps = pmetro.download_map_index(pmetro_url)
pmetro.store_map_index(maps, os.path.join(working_folder, 'maps.json'))
pmetro.download_maps(maps, pmetro_url, working_folder)

