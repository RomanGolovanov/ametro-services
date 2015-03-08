def as_point_list_with_width(text):
    p = as_list(text)
    pts = []
    for i in range(0, len(p) // 2):
        x = float(p[i * 2])
        y = float(p[i * 2 + 1])
        pts.append((x, y))
    if len(p) % 2 == 0:
        width = 1
    else:
        width = p[len(p) - 1]

    if width == '':
        width = 0

    return pts, width


def as_point_list(text=''):
    p = as_list(text)
    lst = []
    for x in range(0, len(p) // 2):
        lst.append((float(p[x * 2]), float(p[x * 2 + 1])))
    return lst


def as_int_point_list(text=''):
    p = as_list(text)
    lst = []
    for x in range(0, len(p) // 2):
        lst.append((int(p[x * 2]), int(p[x * 2 + 1])))
    return lst


def as_int_rect_list(text=''):
    p = as_list(text)
    lst = []
    for x in range(0, len(p) // 4):
        rect = (int(p[x * 4]), int(p[x * 4 + 1]), int(p[x * 4 + 2]), int(p[x * 4 + 3]))
        lst.append(rect)
    return lst


def as_int_rect(text=''):
    if text is None or text.strip() == '':
        return None
    top, left, width, height = as_list(text)
    return [top, left, width, height]


def as_dict(text=''):
    lst = as_quoted_list(text)
    obj = dict()
    for x in range(0, len(lst) // 2):
        obj[lst[x * 2]] = lst[x * 2 + 1]
    return obj


def as_list(text='', splitter=','):
    parts = text.split(splitter)
    lst = []
    for p in parts:
        lst.append(p.strip())
    return lst


def as_float_list(text='', splitter=','):
    if text is None or len(text) == 0:
        return None

    parts = text.split(splitter)
    lst = []
    for p in parts:
        lst.append(float(p.strip()))
    return lst


def as_int_list(text='', splitter=','):
    if text is None or len(text) == 0:
        return []
    parts = text.split(splitter)
    lst = []
    for p in parts:
        lst.append(int(p.strip()))
    return lst


def as_points(items):
    pts = list(items)
    points = []
    for x in range(0, len(pts) // 2):
        points.append((float(pts[x * 2]), float(pts[x * 2 + 1])))
    return points


def as_delay(text):
    if text is None or len(text.strip()) == 0:
        return None
    fp = float(text)
    minutes = int(fp)
    seconds = int((fp - minutes) * 100)
    return minutes * 60 + seconds


def as_delay_list(text):
    if text is None or len(text.strip()) == 0:
        return None
    delays = []
    for d in as_list(text):
        delays.append(as_delay(d))
    return delays


def as_rgb(text=''):
    if text == '0' or text == '00' or text == 'afyh22':
        return '#000'

    if text == '-1' or text == '':
        return 'none'

    if len(text) > 6:
        text = text[:6]

    if len(text) == 6 and text[0] == text[1] and text[2] == text[3] and text[4] == text[5]:
        return '#' + text[0] + text[2] + text[4]

    return '#' + text


def as_quoted_list(line, separator=','):
    if line is None or len(line) == 0:
        return []

    parts = []
    current = []
    length = len(line)
    pos = 0

    quoted = False
    ch = None

    while pos < length:
        previous_ch = ch
        ch = line[pos]
        pos += 1

        if ch == '"':
            quoted = not quoted
            current.append(ch)
            continue

        if quoted or ch != separator:
            current.append(ch)
            continue

        parts.append(''.join(current))
        current = []

    if any(current):
        parts.append(''.join(current))

    return parts


def un_bugger_for_float(text):
    if text is None or len(text) == 0:
        return None
    text = text.strip()
    if ' ' in text:
        return text.split(' ')[0]
    return text