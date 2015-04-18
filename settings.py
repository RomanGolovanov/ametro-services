import os

from globalization.builder import build_geonames_database
from pmetro import ini_files
from pmetro import pmz_transports
from pmetro.log import CompositeLog, LogLevel, ConsoleLog, FileLog

base_dir = ''

FORCE_REFRESH = True
FORCE_IMPORT = True

CACHE_PATH = os.path.join(base_dir, 'cache')
IMPORT_PATH = os.path.join(base_dir, 'www')
TEMP_PATH = os.path.join(base_dir, 'tmp')

MAPS_SOURCE_URL = 'http://pub.skiif.org/pmetro-mirror/'

APP_LOG = CompositeLog([
    ConsoleLog(level=LogLevel.Info),
    FileLog(file_path='import.verbose.log', level=LogLevel.Debug),
    FileLog(file_path='import.info.log', level=LogLevel.Info),
    FileLog(file_path='import.warnings.log', level=LogLevel.Warning),
    FileLog(file_path='import.errors.log', level=LogLevel.Error)
])

ini_files.LOG = APP_LOG
pmz_transports.LOG = APP_LOG

build_geonames_database('geonames')

