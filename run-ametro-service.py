#!/usr/bin/python
# -*- coding: utf-8 -*-

import pmetro
import os

working_folder = 'maps'
if not os.path.isdir(working_folder):
    os.mkdir(working_folder)

maps = pmetro.download_map_index('http://pmetro.chpeks.com/')
pmetro.store_map_index(maps, os.path.join(working_folder, 'maps.json'))
pmetro.download_map_index_files(maps, working_folder)

