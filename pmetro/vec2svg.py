# -*- coding: utf-8 -*-
import string

import svgwrite

from pmetro.files import read_all_lines
from pmetro.helpers import as_list, as_point_list_with_width, as_rgb, as_point_list
from pmetro.graphics import vector_sub, vector_mul_s, vector_mod, vector_add, vector_rotate, cubic_interpolate, \
    vector_left, vector_right

UNKNOWN_COMMANDS = []


def convert_vec_to_svg(vec_file, svg_file):
    style = {
        'brush': 'none',
        'pen': 'none',
        'opaque': 100,
        'size': (0, 0),
        'angle': 0
    }

    container_commands = {
        'angle': __vec_cmd_angle,
    }

    commands = {
        'pencolor': __vec_cmd_pen_color,
        'brushcolor': __vec_cmd_brush_color,
        'opaque': __vec_cmd_opaque,
        'line': __vec_cmd_line,
        'spline': __vec_cmd_spline,
        'polygon': __vec_cmd_polygon,
        'angletextout': __vec_cmd_angle_text_out,
        'stairs': __vec_cmd_stairs,
        'arrow': __vec_cmd_arrow,
        'dashed': __vec_cmd_line_dashed,
        'railway': __vec_cmd_railway
        # 'image,' 'railway', 'ellipse', 'textout', 'spotrect', 'spotcircle
    }

    lines = read_all_lines(vec_file)
    dwg, root = __vec_create_drawing(lines[0], style)
    for l in lines[1:]:
        line = unicode(l).strip()
        if line is None or len(line) == 0 or line.startswith(';') or not (' ' in line):
            style['pen'] = 'black'
            continue

        space_index = line.index(' ')
        cmd = line[:space_index].lower().strip()
        txt = line[space_index:].strip()

        if cmd not in commands and cmd not in container_commands:
            if cmd not in UNKNOWN_COMMANDS:
                UNKNOWN_COMMANDS.append(cmd)
            continue

        if cmd in container_commands:
            root = container_commands[cmd](dwg, root, txt, style)
        else:
            commands[cmd](dwg, root, txt, style)

    dwg.saveas(svg_file)


def __vec_create_drawing(text, style):
    if text.lower().startswith('size'):
        w, h = as_list(text[text.index(' '):].strip(), 'x')
    else:
        w, h = ('0', '0')
    style['size'] = (int(w), int(h))
    w, h = style['size']
    dwg = svgwrite.Drawing(size=(str(w * 2) + 'px', str(h * 2) + 'px'), profile='tiny')
    translate = 'translate(%s %s)' % (w / 2, h / 2)
    g = dwg.g(transform=translate)
    dwg.add(g)
    return dwg, g


def __vec_cmd_angle(dwg, root, text, style):
    angle = float(text)
    current_angle = style['angle']
    style['angle'] = angle
    w, h = style['size']
    rotate = 'rotate(%s,%s,%s)' % (current_angle - angle, w / 2, h / 2)
    new_root = dwg.g(transform=rotate)
    root.add(new_root)
    return new_root


def __vec_cmd_angle_text_out(dwg, root, text, style):
    p = as_list(text.strip('\''))
    angle = float(p[0])
    font_style = p[1]
    font_size = p[2]
    font_weight = 'normal'
    x = float(p[3])
    y = float(p[4])
    pos = (x, y)
    rotate_and_shift = 'rotate(%s %s,%s) translate(0 %s)' % (-angle, x, y, font_size)
    txt = string.join(p[5:], ' ')
    if txt.endswith(' 1'):
        txt = txt[:-2]
        font_weight = 'bold'
    txt = txt.strip('\'')

    root.add(dwg.text(text=txt,
                      insert=pos,
                      font_family=font_style,
                      font_size=font_size,
                      font_weight=font_weight,
                      transform=rotate_and_shift,
                      fill=style['pen'],
                      opacity=style['opaque']))


def __vec_cmd_polygon(dwg, root, text, style):
    pts, width = as_point_list_with_width(text)
    root.add(dwg.polygon(points=pts,
                         stroke=style['pen'],
                         stroke_width=width,
                         fill=style['brush'],
                         opacity=style['opaque']))


def __vec_cmd_line(dwg, root, text, style):
    pts, width = as_point_list_with_width(text)
    root.add(dwg.polyline(points=pts,
                          stroke=style['pen'],
                          stroke_width=width,
                          fill='none',
                          opacity=style['opaque']))


def __vec_cmd_spline(dwg, root, text, style):
    pts, width = as_point_list_with_width(text)
    c = cubic_interpolate(pts)
    root.add(dwg.polyline(points=c,
                          stroke=style['pen'],
                          stroke_width=width,
                          fill='none',
                          opacity=style['opaque']))


def __vec_cmd_line_dashed(dwg, root, text, style):
    pts, width = as_point_list_with_width(text)
    root.add(dwg.polyline(points=pts,
                          stroke=style['pen'],
                          stroke_width=width,
                          stroke_dasharray='5,5',
                          fill='none',
                          opacity=style['opaque']))


def __vec_cmd_opaque(dwg, root, text, style):
    style['opaque'] = float(text) / 100


def __vec_cmd_brush_color(dwg, root, text, style):
    style['brush'] = as_rgb(text)


def __vec_cmd_pen_color(dwg, root, text, style):
    style['pen'] = as_rgb(text)


def __vec_cmd_stairs(dwg, root, text, style):
    start, end, target = as_point_list(text)

    step_length = 4
    path_vec = vector_sub(target, start)
    step_vec = vector_mul_s(path_vec, step_length / vector_mod(path_vec))
    step_count = int(vector_mod(path_vec)) / step_length + 1

    for it in range(0, step_count):
        root.add(dwg.polyline(points=(start, end),
                              stroke=style['pen'],
                              stroke_width=1,
                              fill='none',
                              opacity=style['opaque']))

        start = vector_add(start, step_vec)
        end = vector_add(end, step_vec)


def __vec_cmd_arrow(dwg, root, text, style):
    pts, width = as_point_list_with_width(text)
    root.add(dwg.polyline(points=pts,
                          stroke=style['pen'],
                          stroke_width=width,
                          fill='none',
                          opacity=style['opaque']))

    start = pts[len(pts) - 2]
    end = pts[len(pts) - 1]

    angle = 20
    v = vector_mul_s(vector_sub(start, end), 0.3)

    left_side = vector_add(vector_rotate(v, angle), end)
    right_side = vector_add(vector_rotate(v, -angle), end)

    root.add(dwg.polygon(points=[right_side, end, left_side],
                         stroke=style['pen'],
                         stroke_width=width,
                         fill=style['pen'],
                         opacity=style['opaque']))


def __vec_cmd_railway(dwg, root, text, style):
    w1, w2, h1, x0, y0, x1, y1 = as_list(text)

    start = (float(x0), float(y0))
    end = (float(x1), float(y1))

    v1 = vector_sub(start, end)

    step_length = int(h1)
    step_vec = vector_mul_s(v1, step_length / vector_mod(v1))
    step_count = int(vector_mod(v1)) / step_length + 1

    s1 = vector_mul_s(vector_right(v1), float(w1))
    s2 = vector_mul_s(vector_left(v1), (float(w2) - float(w1)) / 2)
    s3 = vector_mul_s(vector_right(v1), float(w1) + (float(w2) - float(w1)) / 2)

    start2 = vector_add(start, s1)
    end2 = vector_add(end, s1)

    left = vector_add(vector_add(end, s2), step_vec)
    right = vector_add(vector_add(end, s3), step_vec)

    root.add(dwg.polyline(points=(start, end),
                          stroke=style['pen'],
                          stroke_width=1,
                          fill='none',
                          opacity=style['opaque']))

    root.add(dwg.polyline(points=(start2, end2),
                          stroke=style['pen'],
                          stroke_width=1,
                          fill='none',
                          opacity=style['opaque']))

    for it in range(0, step_count - 1):
        root.add(dwg.polyline(points=(left, right),
                              stroke=style['pen'],
                              stroke_width=1,
                              fill='none',
                              opacity=style['opaque']))

        left = vector_add(left, step_vec)
        right = vector_add(right, step_vec)