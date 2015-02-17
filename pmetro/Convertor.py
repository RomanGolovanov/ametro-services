# -*- coding: utf-8 -*-
import os
import shutil
import string

import svgwrite
from pmetro.ConvertorHelpers import as_list, as_point_list_with_width, as_rgb, as_point_list

from pmetro.Math2D import vector_sub, vector_mul_s, vector_mod, vector_add, vector_rotate

UNKNOWN_COMMANDS = []


def convert_files_in_folder(src_path, dst_path):
    if not os.path.isdir(dst_path):
        os.mkdir(dst_path)

    converters = {
        'vec': (convert_vec_to_svg, 'svg')
    }

    for src_name in os.listdir(src_path):
        src_file_path = os.path.join(src_path, src_name)
        if not (os.path.isfile(src_file_path)):
            continue

        src_file_ext = src_file_path[-3:]
        if src_file_ext in converters:
            dst_file_path = os.path.join(dst_path, src_name[:-3] + converters[src_file_ext][1])
            print "Converting %s into %s" % (src_file_path, dst_file_path)
            converters[src_file_ext][0](src_file_path, dst_file_path)
        else:
            dst_file_path = os.path.join(dst_path, src_name)
            print 'Copy %s into %s' % (src_file_path, dst_file_path)
            shutil.copy(src_file_path, dst_file_path)

    print 'Unknown commands: %s' % UNKNOWN_COMMANDS


def convert_vec_to_svg(vec_file, svg_file):
    lines = open(vec_file, 'r').read().decode('windows-1251').encode('utf-8').split('\n')

    style = {
        'brush': 'none',
        'pen': 'none',
        'opaque': 100,
        'size': (0,0),
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
        'spline': __vec_cmd_line,
        'polygon': __vec_cmd_polygon,
        'angletextout': __vec_cmd_angle_text_out,
        'stairs': __vec_cmd_stairs,
        'arrow': __vec_cmd_arrow
        # dashed
        # image
        # railway
        # ellipse
        # textout
        # spotrect
        # spotcircle
    }

    dwg = __vec_create_drawing(lines[0], style)
    root = dwg

    for l in lines[1:]:
        line = str(l).strip()
        if line is None or len(line) == 0 or line.startswith(';') or not (' ' in line):
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
    w, h = as_list(text[text.index(' '):].strip(), 'x')
    style['size'] = (int(w), int(h))
    return svgwrite.Drawing(size=(w + 'px', h + 'px'), profile='tiny')


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
    angle = int(p[0])
    font_style = p[1]
    font_size = p[2]
    font_weight = 'normal'
    x = int(p[3])
    y = int(p[4])
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

