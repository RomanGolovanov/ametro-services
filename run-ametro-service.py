#!/usr/bin/python
# -*- coding: utf-8 -*-

import pmetro
import os

working_folder = 'maps'
if not os.path.isdir(working_folder):
    os.mkdir(working_folder)

pmetro_url = 'http://pmetro.chpeks.com/'

pmetro.update_maps_cache(pmetro_url, working_folder)
