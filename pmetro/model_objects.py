class MapContainer(object):
    def __init__(self):
        self.delays = []
        self.transports = []
        self.schemes = []
        self.images = []
        self.texts = []


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
        self.background=''
        self.station_diameter = 1
        self.line_width = 1
        self.upper_case = False
        self.word_wrap = False
        self.is_vector = False
        self.transports = []
        self.default_transports = []

        self.lines = []

