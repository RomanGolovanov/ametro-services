#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import pmetro

base_dir = ''

cache_path = os.path.join(base_dir, 'cache')
publication_path = os.path.join(base_dir, 'www')
temp_path = os.path.join(base_dir, 'tmp')

pmetro_url = 'http://pmetro.chpeks.com/'

pmetro.refresh_cache(cache_path, pmetro_url)
pmetro.update_publication(cache_path, publication_path, temp_path)