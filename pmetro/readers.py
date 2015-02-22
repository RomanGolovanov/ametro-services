from pmetro.files import read_all_lines
from pmetro.log import ConsoleLog

LOG = ConsoleLog()


class IniReader(object):
    def __init__(self):
        self.lines = []
        self.position = 0

    def open(self, path):
        self.lines = read_all_lines(path)
        self.position = 0

    def section(self, section):
        index = 0
        pattern = '[' + section + ']'
        while index < len(self.lines):
            if self.lines[index].strip().lower() == pattern.lower():
                self.position = index
                return
            index += 1
        raise 'No section ' + section + ' found'

    def read(self):
        if self.position is None:
            self.position = 0
        else:
            self.position += 1

        if self.position >= len(self.lines):
            return False

        line = self.lines[self.position].strip()
        if line.startswith('[') and line.endswith(']'):
            return False

        return True

    def name(self):
        return self.lines[self.position].strip().lower().split('=')[0]

    def value(self):
        return self.lines[self.position].strip().split('=')[1]


def deserialize_ini(file_path):
    pos = 0
    obj = {}
    default_section = {}
    section = default_section
    for line in read_all_lines(file_path):
        pos += 1

        line = str(line).strip().replace('\\n', '\n')
        cleaned = line.lower()

        if len(cleaned) == 0 or cleaned[0] == ';':
            continue

        if cleaned.startswith('[') and cleaned.endswith(']'):
            name = line.strip('[').strip(']').strip()
            if len(name) == 0:
                continue

            section = {}
            obj[name] = section
            continue

        if '=' in cleaned:
            index = cleaned.index('=')
            name = line[:index].strip()
            value = line[index + 1:].strip()
            if name in section:
                section[name] = section[name] + '\n' + value
            else:
                section[name] = value
            continue

        LOG.warning('Invalid text [%s] at line %s in %s' % (line.replace('\n', ''), pos - 1, file_path))

    if any(default_section.keys()):
        LOG.warning('Unnamed section in %s' % file_path)
        obj['__Default__'] = default_section

    return obj


def get_ini_attr(ini_obj, section_name, prop_name, default_value=None):
    section = get_ini_section(ini_obj, section_name)
    if section is None or prop_name not in section:
        return default_value
    return section[prop_name]


def get_ini_attr_collection(ini_obj, section_name, prop_name_prefix):
    section = get_ini_section(ini_obj, section_name)
    if section is None:
        return None
    copy = {}
    for attr in section:
        if str(attr).startswith(prop_name_prefix):
            copy[attr] = section[attr]
    return copy


def get_ini_section(ini_obj, section_name):
    if section_name not in ini_obj:
        return None
    return ini_obj[section_name]


def get_ini_sections(ini_obj, section_name_prefix):
    sections = []
    for name in ini_obj:
        if str(name).startswith(section_name_prefix):
            sections.append(name)
    return sections
