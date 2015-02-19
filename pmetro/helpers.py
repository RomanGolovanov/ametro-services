# -*- coding: utf-8 -*-

def as_point_list_with_width(text):
    p = as_list(text)
    pts = []
    for i in range(0, len(p) / 2):
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
    for x in range(0, len(p) / 2):
        lst.append((float(p[x * 2]), float(p[x * 2 + 1])))
    return lst


def as_list(text='', splitter=','):
    parts = text.split(splitter)
    lst = []
    for p in parts:
        lst.append(p.strip())
    return lst


def as_points(items):
    pts = list(items)
    points = []
    for x in range(0, len(pts) / 2):
        points.append( (float(pts[x * 2]), float(pts[x * 2 + 1])) )
    return points


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

