class MapTransfer(object):
    def __init__(self):
        self.name = ''
        self.from_line = ''
        self.from_station = ''
        self.to_line = ''
        self.to_station = ''
        self.delay = None
        self.state = None


class MapLine(object):
    def __init__(self):
        self.id = ''
        self.name = ''
        self.map = ''
        self.stations = []
        self.segments = []


class MapTransport(object):
    def __init__(self):
        self.name = ''
        self.type = ''
        self.lines = []
        self.transfers = []


class MapContainer(object):
    def __init__(self):
        self.delays = []
        self.transports = []
        self.stations = []
        self.images = []
        self.maps = []
        self.texts = []
