import os
from globalization.database import create_geonames_database

create_geonames_database(os.path.join(os.path.dirname(__file__), 'globalization'), 'geonames')