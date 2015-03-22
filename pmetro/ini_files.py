import uuid
from pmetro.file_utils import read_all_lines
from pmetro.log import ConsoleLog

LOG = ConsoleLog()

__DUPLICATES_SAFE_FILES = {
    '.cty',
    '.txt'
}


def deserialize_ini(file_path):
    pos = 0
    obj = {
        '__FILE_NAME__': file_path,
        '__DEFAULT__': None
    }
    default_section = {}
    section = default_section
    for line in read_all_lines(file_path):
        pos += 1

        line = str(line).strip().replace('\\n', '\n')
        cleaned = line.lower()

        if len(cleaned) == 0 or cleaned[0] == ';':
            continue

        if cleaned == '[]':
            LOG.info('Empty section [] detected in file %s at line %s, stop reading file' % (file_path, pos))
            break

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
        else:
            name = line
            value = '1'

        if len(name) == 0:
            name = uuid.uuid1().hex

        if name in section:
            composite_name = __create_composite_name(name)
            if composite_name not in section:

                if not any((ext for ext in __DUPLICATES_SAFE_FILES if file_path.endswith(ext))):
                    LOG.warning('Duplicate parameter name \'%s\' found in file %s at line %s' % (name, file_path, pos))

                section[composite_name] = section[name]
            section[composite_name] = section[composite_name] + '\n' + value
        else:
            section[name] = value
        continue

    if any(default_section.keys()):
        LOG.warning('Some properties not in named section in file \'%s\'' % file_path)
        obj['__DEFAULT__'] = default_section

    return obj


def __create_composite_name(name):
    return '__' + name + '_COMPOSITE__'


def get_ini_attr_bool(ini, section_name, prop_name, default_value=None):
    value = get_ini_attr(ini, section_name, prop_name, None)
    if value is None:
        return default_value

    return value.strip().lower() == 'true'


def get_ini_attr_int(ini, section_name, prop_name, default_value=None):
    return int(get_ini_attr(ini, section_name, prop_name, default_value))


def get_ini_attr_float(ini, section_name, prop_name, default_value=None):
    return float(get_ini_attr(ini, section_name, prop_name, default_value))


def get_ini_attr(ini_obj, section_name, prop_name, default_value=None):
    section = get_ini_section(ini_obj, section_name)
    if section is None or prop_name not in section:
        return default_value
    return section[prop_name]


def get_ini_composite_attr(ini, section_name, prop_name, default_value=None):
    attr = get_ini_attr(ini, section_name, __create_composite_name(prop_name), default_value)
    if attr is not None:
        return attr
    return get_ini_attr(ini, section_name, prop_name, default_value)


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
