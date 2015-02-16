# -*- coding: utf-8 -*-

import codecs
import string
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
        'angletextout': __vec_cmd_angletextout
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


def __vec_cmd_angletextout(dwg=svgwrite.Drawing(), text='', style={}):
    print text
    p = __as_list(text)
    angle = int(p[0])
    font_style = p[1]
    font_size = p[2]
    x = int(p[3])
    y = int(p[4])
    position=(x,y)
    r = 'rotate(%s %s,%s) translate(0 %s)' % (-angle,x,y,font_size)
    txt = string.join(p[5:], ' ')

    dwg.add(dwg.text(text=txt,
                     insert=position,
                     font_family=font_style,
                     font_size=font_size,
                     fill=style['pen'],
                     transform=r,
                     opacity=style['opaque']))
    return dwg


def __vec_cmd_polygon(dwg=svgwrite.Drawing(), text='', style={}):
    p = __as_list(text)
    pts = []
    for x in range(0, len(p) / 2):
        pts.append((p[x * 2], p[x * 2 + 1]))
    if len(p) % 2 == 0:
        width = 1
    else:
        width = p[len(p) - 1]
    # print 'polygon %s (w=%s)' % (pts, width)
    dwg.add(
        dwg.polygon(points=pts, stroke=style['pen'], stroke_width=width, fill=style['brush'], opacity=style['opaque']))
    return dwg


def __vec_cmd_line(dwg=svgwrite.Drawing(), text='', style={}):
    p = __as_list(text)
    pts = []
    for x in range(0, len(p) / 2):
        pts.append((p[x * 2], p[x * 2 + 1]))
    if len(p) % 2 == 0:
        width = 1
    else:
        width = p[len(p) - 1]
    # print 'polyline %s (w=%s)' % (pts, width)
    dwg.add(dwg.polyline(points=pts, stroke=style['pen'], stroke_width=width, fill='none', opacity=style['opaque']))
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
    d = __as_list(text, 'x')
    return svgwrite.Drawing(size=(d[0] + 'px', d[1] + 'px'), profile='tiny')


def __as_list(text='', splitter=','):
    parts = text.split(splitter)
    r = []
    for p in parts:
        r.append(p.strip())
    return r


def __as_rgb(text=''):
    if text == '-1':
        return 'none'
    return 'rgb(%s,%s,%s)' % (int('0x' + text[:2], 0), int('0x' + text[2:4], 0), int('0x' + text[4:], 0))




