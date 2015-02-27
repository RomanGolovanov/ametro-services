class MapMetadata(object):
    def __init__(self, map_info, delays):
        self.map_id = map_info['city']
        self.city = map_info['city']
        self.country = map_info['country']
        self.iso = map_info['iso']
        self.file = map_info['file']
        self.latitude = map_info['latitude']
        self.longitude = map_info['longitude']
        self.version = map_info['version']
        self.geo_name_id = map_info['id']
        self.description = map_info['description']
        self.comments = map_info['comments']        
        self.delays = delays
        self.transport_types = []
        self.transports = []
        self.schemes = []


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
    def __init__(self):
        self.name = ''
        self.type = ''
        self.lines = []
        self.transfers = []


class MapTransportLine(object):
    def __init__(self):
        self.name = ''
        self.alias = ''
        self.map = ''
        self.stations = []
        self.segments = []
        self.aliases = []


class MapScheme(object):
    def __init__(self):
        self.name = ''
        self.images = []
        self.stations_diameter = 11
        self.upper_case = True
        self.word_wrap = True
        self.transports = []
        self.default_transports = []

        self.lines = []


class MapSchemeLine(object):
    def __init__(self):
        self.name = ''
        self.line_color = 0
        self.line_width = 9
        self.labels_color = 0
        self.labels_bg_color = 0
        self.rect = (0,0,0,0)
        self.stations = []
        self.segments = []


class MapSchemeStation(object):
    def __init__(self):
        self.name = None
        self.coord = None
        self.rect = None
