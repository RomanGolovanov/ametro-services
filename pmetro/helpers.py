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
    for x in range(0, len(p) / 2):
        yield (float(p[x * 2]), float(p[x * 2 + 1]))


def as_list(text='', splitter=','):
    parts = text.split(splitter)
    lst = []
    for p in parts:
        lst.append(p.strip())
    return lst


def as_rgb(text=''):
    if text == '0':
        return '#000'
    if text == '-1':
        return 'none'
    if text == '':
        return 'none'
    return '#' + text

