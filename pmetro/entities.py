
class MapMetadata(object):
    def __init__(self, geoname_id, file_name, timestamp, latitude, longitude, description, comments):
        self.map_id = file_name
        self.geoname_id = geoname_id
        self.file = file_name
        self.timestamp = timestamp
        self.latitude = latitude
        self.longitude = longitude
        self.description = description
        self.comments = comments
        self.delays = []
        self.transport_types = []
        self.transports = []
        self.schemes = []
        self.locales = []
        self.default_locale = None


class MapContainer(object):
    def __init__(self):
        self.meta = None
        self.transports = []
        self.schemes = []
        self.images = []
        self.texts = []


class MapImage(object):
    def __init__(self):
        self.caption = ''
        self.line = ''
        self.station = ''
        self.image = ''


class MapTransport(object):
    def __init__(self, name='', type_name='', lines=None, transfers=None):
        if not lines:
            lines = []
        if not transfers:
            transfers = []
        self.name = name
        self.type_name = type_name
        self.lines = lines
        self.transfers = transfers


class MapTransportLine(object):
    def __init__(self, name, text_id, scheme, stations, segments, delays):
        self.name = name
        self.text_id = text_id
        self.scheme = scheme
        self.stations = stations
        self.segments = segments
        self.delays = delays


class MapScheme(object):
    def __init__(self):
        self.name = ''
        self.name_text_id = ''
        self.type_text_id = ''
        self.width = 0
        self.height = 0
        self.images = []
        self.stations_diameter = 11
        self.lines_width = 9
        self.upper_case = True
        self.word_wrap = True
        self.transports = []
        self.default_transports = []
        self.lines = []
        self.is_vector = True


class MapSchemeLine(object):
    def __init__(self, name, text_id, line_color, line_width, labels_color, labels_bg_color, stations, segments):
        self.name = name
        self.text_id = text_id
        self.line_color = line_color
        self.line_width = line_width
        self.labels_color = labels_color
        self.labels_bg_color = labels_bg_color
        self.stations = stations
        self.segments = segments


class MapSchemeStation(object):
    def __init__(self):
        self.uid = 0
        self.name = None
        self.text_id = None
        self.coord = None
        self.rect = None
        self.is_working = None
