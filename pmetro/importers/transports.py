import os
from pmetro import ini_files
from pmetro import files
from pmetro import model_objects
from pmetro import helpers
from pmetro import model_transports


class PmzTransportImporter(object):
    def __init__(self, path, meta, get_station_uid_func, get_line_uid_func, strings_dict):
        self.path = path
        self.meta = meta
        self.__get_station_uid_func = get_station_uid_func
        self.__get_line_uid_func = get_line_uid_func
        self.strings_dict = strings_dict

    def import_transports(self):

        transport_files = sorted(files.find_files_by_extension(self.path, '.trp'))
        if not any(transport_files):
            raise FileNotFoundError('Cannot found .trp files in %s' % self.path)

        default_file = os.path.join(self.path, 'Metro.trp')
        if default_file not in transport_files:
            raise FileNotFoundError('Cannot found Metro.trp file in %s' % self.path)

        return [self.__import_transport(default_file)] + \
               [self.__import_transport(x) for x in transport_files if x != default_file]


    def __import_transport(self, path):
        ini = ini_files.deserialize_ini(path)
        name = files.get_file_name_without_ext(path).lower()
        return model_objects.MapTransport(
            name,
            model_transports.get_transport_type(self.meta.file, name, ini),
            self.__import_lines(ini),
            self.__import_transfers(ini)
        )

    def __import_lines(self, ini):
        sections = ini_files.get_ini_sections(ini, 'Line')
        if not any(sections):
            return []

        lines = []
        for section_name in sorted(sections):
            line_name = ini_files.get_ini_attr(ini, section_name, 'Name')
            line_uid = self.__get_line_uid_func(line_name)

            line_map = ini_files.get_ini_attr(ini, section_name, 'LineMap')
            stations_text = ini_files.get_ini_attr(ini, section_name, 'Stations')
            drivings_text = ini_files.get_ini_attr(ini, section_name, 'Driving')
            aliases_text = ini_files.get_ini_attr(ini, section_name, 'Aliases')

            (skipped_stations, raw_segments) = model_transports.parse_station_and_delays(stations_text, drivings_text)

            alias_dict = {}
            if aliases_text is not None and len(aliases_text) != 0:
                alias_dict = helpers.as_dict(aliases_text)

            self.strings_dict[line_uid] = ini_files.get_ini_attr(ini, section_name, 'Alias', line_name)
            stations = []
            for station_name, station_display_name in self.__get_stations(stations_text):
                station_uid = self.__get_station_uid_func(line_name, station_name)
                stations.append(station_uid)
                if station_display_name in alias_dict:
                    self.strings_dict[station_uid] = alias_dict[station_display_name]
                else:
                    self.strings_dict[station_uid] = station_display_name

            segments = []
            for station_from, station_to, delay in raw_segments:
                segments.append((stations[station_from], stations[station_to], delay ))

            lines.append(model_objects.MapTransportLine(
                line_uid,
                files.get_file_name_without_ext(line_map).lower() if line_map is not None else None,
                stations,
                segments,
                model_transports.parse_line_delays(ini_files.get_ini_attr_collection(ini, section_name, 'Delay'))
            ))

        return lines

    def __import_transfers(self, ini):
        section = ini_files.get_ini_section(ini, 'Transfers')
        if section is None:
            return []
        return list(self.__parse_transfers(section))

    def __parse_transfers(self, section):
        for name in sorted(section):
            if str(name).startswith('__'):
                continue
            params = helpers.as_quoted_list(section[name])
            from_uid = self.__get_station_uid_func(params[0], params[1])
            to_uid = self.__get_station_uid_func(params[2], params[3])

            if len(params) > 4:
                # TODO: FIX SOURCE!
                delay = float(helpers.un_bugger_for_float(params[4]))
            else:
                delay = None

            if len(params) > 5:
                flag = params[5]
            else:
                flag = 'visible'
            yield from_uid, to_uid, delay, flag

    @staticmethod
    def __get_stations(stations_text):
        stations = []
        stations_iter = model_transports.StationsString(stations_text)
        quoted = False
        while stations_iter.has_next():

            if stations_iter.next_separator == '(':
                quoted = True

            if stations_iter.next_separator == ')':
                quoted = False

            station, original_station = stations_iter.next()

            if not quoted:
                stations.append((station, original_station))

        return stations
