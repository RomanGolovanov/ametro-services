from pmetro import model_objects
from pmetro.importers import transports


class PmzImporter(object):
    def __init__(self, path, map_info):
        self.__path = path
        self.__map_info = map_info
        self.__map_container = model_objects.MapContainer()
        self.__map_container.meta = model_objects.MapMetadata(self.__map_info)

        self.__uid_counter = 0
        self.__station_uid_dict = dict()
        self.__line_uid_dict = dict()

        self.strings_dict = dict()

        self.__transport_importer = transports.PmzTransportImporter(
            path,
            self.__map_container.meta,
            self.__get_station_uid,
            self.__get_line_uid,
            self.strings_dict
        )

    def import_pmz(self):
        self.__map_container.transports = self.__transport_importer.import_transports()

        return self.__map_container

    def __get_station_uid(self, line, station):
        if (line, station) not in self.__station_uid_dict:
            self.__uid_counter += 1
            self.__station_uid_dict[(line, station)] = self.__uid_counter
        return self.__station_uid_dict[(line, station)]

    def __get_line_uid(self, line):
        if line not in self.__line_uid_dict:
            self.__uid_counter += 1
            self.__line_uid_dict[line] = self.__uid_counter
        return self.__line_uid_dict[line]

