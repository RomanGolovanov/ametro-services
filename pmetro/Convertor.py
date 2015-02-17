# -*- coding: utf-8 -*-

import string
import math

import svgwrite


def convert_vec_to_svg(vec_file, svg_file):
    lines = open(vec_file, 'r').read().decode('windows-1251').encode('utf-8').split('\n')

    dwg = svgwrite.Drawing()

    style = {
        'brush': 0,
        'pen': 0,
        'opaque': 100,
    }
    commands = {
        'size': __vec_cmd_size,
        'pencolor': __vec_cmd_pen_color,
        'brushcolor': __vec_cmd_brush_color,
        'opaque': __vec_cmd_opaque,
        'line': __vec_cmd_line,
        'spline': __vec_cmd_line,
        'polygon': __vec_cmd_polygon,
        'angletextout': __vec_cmd_angle_text_out,
        'stairs': __vec_cmd_stairs
    }
    unknown = []

    for l in lines:
        line = str(l).strip()
        if line is None or len(line) == 0 or line.startswith(';') or not (' ' in line):
            continue

        space_index = line.index(' ')

        cmd = line[:space_index].lower().strip()
        if not (cmd in commands):
            if cmd not in unknown:
                unknown.append(cmd)
            continue

        dwg = commands[cmd](dwg, line[space_index:].strip(), style)

    dwg.saveas(svg_file)
    print "Complete. Unknown commands: %s" % unknown


def __vec_cmd_angle_text_out(dwg=svgwrite.Drawing(), text='', style={}):
    p = __as_list(text.strip('\''))
    angle = int(p[0])
    font_style = p[1]
    font_size = p[2]
    x = int(p[3])
    y = int(p[4])
    pos = (x, y)
    rotate_and_shift = 'rotate(%s %s,%s) translate(0 %s)' % (-angle, x, y, font_size)
    txt = string.join(p[5:], ' ')

    dwg.add(dwg.text(text=txt, insert=pos, font_family=font_style, font_size=font_size,
                     fill=style['pen'], transform=rotate_and_shift, opacity=style['opaque']))
    return dwg


def __vec_cmd_polygon(dwg=svgwrite.Drawing(), text='', style={}):
    pts, width = __as_point_list_with_width(text)
    dwg.add(dwg.polygon(points=pts,
                        stroke=style['pen'],
                        stroke_width=width,
                        fill=style['brush'],
                        opacity=style['opaque']))
    return dwg


def __vec_cmd_line(dwg=svgwrite.Drawing(), text='', style={}):
    pts, width = __as_point_list_with_width(text)
    dwg.add(dwg.polyline(points=pts,
                         stroke=style['pen'],
                         stroke_width=width,
                         fill='none',
                         opacity=style['opaque']))
    return dwg


def __vec_cmd_opaque(dwg=svgwrite.Drawing(), text='', style={}):
    style['opaque'] = float(text) / 100
    return dwg


def __vec_cmd_brush_color(dwg=svgwrite.Drawing(), text='', style={}):
    style['brush'] = __as_rgb(text)
    return dwg


def __vec_cmd_pen_color(dwg=svgwrite.Drawing(), text='', style={}):
    style['pen'] = __as_rgb(text)
    return dwg


def __vec_cmd_size(dwg=svgwrite.Drawing(), text='', style={}):
    w, h = __as_list(text, 'x')
    return svgwrite.Drawing(size=(w + 'px', h + 'px'), profile='tiny')


def __as_point_list_with_width(text):
    p = __as_list(text)
    pts = []
    for x in range(0, len(p) / 2):
        pts.append((p[x * 2], p[x * 2 + 1]))
    if len(p) % 2 == 0:
        width = 1
    else:
        width = p[len(p) - 1]
    return pts, width


def __as_point_list(text=''):
    p = __as_list(text)
    for x in range(0, len(p) / 2):
        yield (float(p[x * 2]), float(p[x * 2 + 1]))


def __as_list(text='', splitter=','):
    parts = text.split(splitter)
    lst = []
    for p in parts:
        lst.append(p.strip())
    return lst


def __as_rgb(text=''):
    if text == '-1':
        return 'none'
    return 'rgb(%s,%s,%s)' % (int('0x' + text[:2], 0), int('0x' + text[2:4], 0), int('0x' + text[4:], 0))


def __vec_cmd_stairs(dwg=svgwrite.Drawing(), text='', style={}):
    start, end, target = __as_point_list(text)

    v = __as_vector(start, target)
    shift = __vector_mul(v, 1.0 / __vector_len(v) * 10.0)

    for it in range(0, 10):
        dwg.add(dwg.polyline(points=(start, end),
                             stroke=style['pen'],
                             stroke_width=1,
                             fill='none',
                             opacity=style['opaque']))

        start = __vector_add(start, shift)
        end = __vector_add(end, shift)

    return dwg


def __vector_len(vec):
    x, y = vec
    return math.sqrt(x * x + y * y)


def __as_vector(start, end):
    x0, y0 = start
    x1, y1 = end
    return x1 - x0, y1 - y0


def __vector_mul(vec, d):
    x, y = vec
    return x * d, y * d


def __vector_add(vec, dv):
    x, y = vec
    dx,dy = dv
    return x + dx, y + dy