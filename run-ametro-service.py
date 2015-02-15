#!/usr/bin/python
# -*- coding: utf-8 -*-

import pmetro

cache_path = 'cache'
publication_path = 'www'

pmetro_url = 'http://pmetro.chpeks.com/'

pmetro.refresh_cache(cache_path, pmetro_url)
pmetro.update_publication(cache_path, publication_path)