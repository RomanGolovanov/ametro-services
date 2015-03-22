import langdetect
from transliterate import translit, get_available_language_codes


class TextTable(object):
    def __init__(self, texts, language_code):
        self.texts = texts
        self.language_code = language_code


class TextIndexTable(object):
    def __init__(self):
        self.texts = dict()
        self.counter = 100000

    def as_text_id(self, text):
        if text in self.texts:
            return self.texts[text]

        text_id = self.counter
        self.texts[text] = text_id

        self.counter += 1

        return text_id

    def get_text(self, text_id):
        return self.texts.get(text_id, None)

    def get_text_table(self):
        full_text = '. '.join([key for key, value in self.texts.items()])
        return TextTable(
            sorted([(value, key) for key, value in self.texts.items()], key=lambda x: x[0]),
            langdetect.detect(full_text)
        )


def transliterate_text_table_to_en(text_table):
    language_code = text_table.language_code
    if language_code not in get_available_language_codes():
        raise ValueError(
            "Language code " + language_code + " not found in supported transliteration tables " + ",".join(
                get_available_language_codes()))

    return TextTable(
        [(text_id, translit(text, text_table.language_code, reversed=True)) for text_id, text in text_table.texts],
        'en'
    )


class StationIndex(object):
    def __init__(self):
        self.registered_stations = dict()
        self.pending_stations = dict()
        self.id_counter = 0

    def register_station(self, line_name, station_name):
        key = (line_name, station_name)
        if key in self.registered_stations:
            raise ValueError('Station ' + station_name + ' on line ' + line_name + ' already registered')

        if key in self.pending_stations:
            station_id = self.pending_stations[key]
            del self.pending_stations[key]
        else:
            station_id = self.id_counter

        self.registered_stations[key] = station_id
        self.id_counter += 1
        return station_id

    def get_station_id(self, line_name, station_name):
        key = (line_name, station_name)
        if key in self.registered_stations:
            return self.registered_stations[key]

        if key in self.pending_stations:
            station_id = self.pending_stations[key]
        else:
            station_id = self.id_counter
            self.pending_stations[key] = station_id
            self.id_counter += 1

        return station_id

    def find_station_id(self, line_name, station_name):
        key = (line_name, station_name)
        if key in self.registered_stations:
            return self.registered_stations[key]

        if key in self.pending_stations:
            return self.pending_stations[key]

        return None


    def ensure_no_pending_stations(self):
        if not self.pending_stations:
            return

        left_items = ['{0} at {1}'.format(station_name, line_name) for line_name, station_name in self.pending_stations]
        raise ValueError("There are some unresolved pending stations found: " + ", ".join(left_items))
