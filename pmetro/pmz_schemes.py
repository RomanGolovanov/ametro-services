__DEFAULT_SCHEME_TYPE_NAME = 'OTHER'
__ROOT_SCHEME_TYPE_NAME = 'ROOT'

__DEFAULT_LINES_WIDTH = 9
__DEFAULT_STATIONS_DIAMETER = 11

__WELL_KNOWN_SCHEME_TRANSPORTS = {
    'railway': 'trains',
    'tramways': 'trams',
    'rechnoytramvay': 'tramsriver'
}

__WELL_KNOWN_ROOT_SCHEME_TYPES = {
    'metro': 'Метро',
    'railway': 'Электричка',
    'trains': 'Электричка',
    'tramways': 'Трамвай',
    'trams': 'Трамвай',
    'trolleys': 'Троллейбус',
    'tramsriver': 'Речной Трамвай',
    'rechnoytramvay': 'Речной Трамвай'
}


def suggest_scheme_display_name_and_type(name, transport_index, scheme_index, text_index_table):
    if name in transport_index:
        return transport_index[name].type_name, __ROOT_SCHEME_TYPE_NAME

    if name in __WELL_KNOWN_SCHEME_TRANSPORTS:
        suggested_name = __WELL_KNOWN_SCHEME_TRANSPORTS[name]
        if suggested_name in transport_index:
            return transport_index[suggested_name].type_name, __ROOT_SCHEME_TYPE_NAME

    if name in scheme_index:
        trp_line, trp_scheme = scheme_index[name]
        return text_index_table.get_text(trp_line.text_id), trp_scheme.type_name

    if name in __WELL_KNOWN_ROOT_SCHEME_TYPES:
        return __WELL_KNOWN_ROOT_SCHEME_TYPES[name], __ROOT_SCHEME_TYPE_NAME

    return name, __DEFAULT_SCHEME_TYPE_NAME


def create_line_index(transports):
    index = dict()
    for trp in transports:
        for line in trp.lines:
            index[line.name] = line
    return index


def create_scheme_index(transports):
    index = dict()
    for trp in transports:
        for line in [l for l in trp.lines if l.scheme is not None and l.scheme != '']:
            index[line.scheme] = (line, trp)
    return index


def create_transport_index(transports):
    index = dict()
    for trp in transports:
        index[trp.name] = trp
    return index


def create_visible_transfer_list(transports):
    lst = []
    for trp in transports:
        for from_line, from_station, to_line, to_station, delay, flag in trp.transfers:
            if flag.lower() == 'visible':
                lst.append((from_line, from_station, to_line, to_station))
    return lst



