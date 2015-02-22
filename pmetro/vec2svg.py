import codecs
import json

import svgwrite

from pmetro.files import read_all_lines
from pmetro.helpers import as_list, as_point_list_with_width, as_rgb, as_point_list, as_points
from pmetro.graphics import vector_sub, vector_mul_s, vector_mod, vector_add, vector_rotate, cubic_interpolate, \
    vector_left, vector_right
from pmetro.log import EmptyLog


__MAP_EDGE_SIZE = 50
__FONT_WIDTH = 0.3
__FONT_HEIGHT = 0.9


def convert_vec_to_svg(vec_file, svg_file, log=EmptyLog()):
    style = {
        'brush': 'none',
        'pen': 'none',
        'text-color': 'none',
        'opaque': 100,
        'size': (0, 0),
        'rect': (0, 0, 0, 0),
        'angle': 0
    }

    container_commands = {
        'angle': __vec_cmd_angle,
    }

    commands = {
        'size': __vec_cmd_size,
        'pencolor': __vec_cmd_pen_color,
        'brushcolor': __vec_cmd_brush_color,
        'opaque': __vec_cmd_opaque,
        'line': __vec_cmd_line,
        'spline': __vec_cmd_spline,
        'polygon': __vec_cmd_polygon,
        'angletextout': __vec_cmd_angle_text_out,
        'textout': __vec_cmd_text_out,
        'stairs': __vec_cmd_stairs,
        'arrow': __vec_cmd_arrow,
        'dashed': __vec_cmd_line_dashed,
        'railway': __vec_cmd_railway,
        'ellipse': __vec_cmd_ellipse,

        'spotrect': __vec_cmd_empty,
        'spotcircle': __vec_cmd_empty,
        'image':  __vec_cmd_empty
    }

    dwg = svgwrite.Drawing(profile='tiny')
    root_container = dwg.g()
    dwg.add(root_container)
    root = root_container

    line_index = 0
    for l in read_all_lines(vec_file):
        line_index += 1
        line = l.strip()
        if line is None or len(line) == 0 or line.startswith(';') or not (' ' in line):
            style['pen'] = '#000'
            style['text-color'] = '#FFF'
            continue

        space_index = line.index(' ')
        cmd = line[:space_index].lower().strip()
        txt = line[space_index:].strip()

        if cmd not in commands and cmd not in container_commands:
            log.warning('Unknown command [%s] in file %s at line %s' % (cmd, vec_file, line_index - 1))
            continue

        if cmd in container_commands:
            root = container_commands[cmd](dwg, root, txt, style)
        else:
            commands[cmd](dwg, root, txt, style)

    x0, y0, x1, y1 = style['rect']
    w, h = style['size']
    dwg.attribs['width'] = '%spx' % int(x1 - x0 + __MAP_EDGE_SIZE * 2)
    dwg.attribs['height'] = '%spx' % int(y1 - y0 + __MAP_EDGE_SIZE * 2)
    root_container.attribs['transform'] = 'translate(%s,%s)' % ( -x0 + __MAP_EDGE_SIZE, -y0 + __MAP_EDGE_SIZE )

    dwg.saveas(svg_file)

    meta = {'width': w, 'height': h, 'dx': x0 - __MAP_EDGE_SIZE, 'dy': y0 - __MAP_EDGE_SIZE}
    with codecs.open(svg_file + '.meta', 'w', encoding='utf-8') as f:
        f.write(json.dumps(meta, ensure_ascii=False, indent=True))


def __vec_cmd_size(dwg, root, text, style):
    w, h = as_list(text, 'x')
    style['size'] = (int(w), int(h))


def __vec_cmd_angle(dwg, root, text, style):
    angle = float(text)
    style['angle'] += angle
    w, h = style['size']
    rotate = 'rotate(%s,%s,%s)' % (- angle, w / 2, h / 2)
    new_root = dwg.g(transform=rotate)
    root.add(new_root)
    return new_root


def __vec_cmd_text_out(dwg, root, text, style):
    p = as_list(text.strip('\''))
    font_style = p[0]
    font_size = int(p[1])
    font_weight = 'normal'
    x = float(p[2])
    y = float(p[3])
    pos = (x - font_size * __FONT_WIDTH / 2, y + font_size*__FONT_HEIGHT)
    txt = ' '.join(p[4:])
    if txt.endswith(' 1'):
        txt = txt[:-2]
        font_weight = 'bold'
    txt = txt.strip('\'')

    __update_bounding_box((pos, vector_add(pos, (font_size * len(text) * __FONT_WIDTH, 0))), style)
    root.add(dwg.text(text=txt,
                      insert=pos,
                      font_family=font_style,
                      font_size=font_size,
                      font_weight=font_weight,
                      fill=style['text-color'],
                      opacity=style['opaque']))


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
    txt = ' '.join(p[5:])
    if txt.endswith(' 1'):
        txt = txt[:-2]
        font_weight = 'bold'
    txt = txt.strip('\'')

    __update_bounding_box((pos,), style)
    root.add(dwg.text(text=txt,
                      insert=pos,
                      font_family=font_style,
                      font_size=font_size,
                      font_weight=font_weight,
                      transform=rotate_and_shift,
                      fill=style['text-color'],
                      opacity=style['opaque']))


def __vec_cmd_polygon(dwg, root, text, style):
    pts, width = as_point_list_with_width(text)
    __update_bounding_box(pts, style)
    root.add(dwg.polygon(points=pts,
                         stroke=style['pen'],
                         stroke_width=width,
                         fill=style['brush'],
                         opacity=style['opaque']))


def __vec_cmd_line(dwg, root, text, style):
    pts, width = as_point_list_with_width(text)
    __update_bounding_box(pts, style)
    root.add(dwg.polyline(points=pts,
                          stroke=style['pen'],
                          stroke_width=width,
                          fill='none',
                          opacity=style['opaque']))


def __vec_cmd_spline(dwg, root, text, style):
    pts, width = as_point_list_with_width(text)
    __update_bounding_box(pts, style)
    c = cubic_interpolate(pts)
    root.add(dwg.polyline(points=c,
                          stroke=style['pen'],
                          stroke_width=width,
                          fill='none',
                          opacity=style['opaque']))


def __vec_cmd_line_dashed(dwg, root, text, style):
    pts, width = as_point_list_with_width(text)
    __update_bounding_box(pts, style)
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
    style['text-color'] = as_rgb(text)


def __vec_cmd_stairs(dwg, root, text, style):
    start, end, target = as_point_list(text)
    __update_bounding_box((start, end, target), style)

    step_length = 4
    path_vec = vector_sub(target, start)
    step_vec = vector_mul_s(path_vec, step_length / vector_mod(path_vec))
    step_count = int(vector_mod(path_vec)) // step_length + 1

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
    __update_bounding_box(pts, style)

    start = pts[len(pts) - 2]
    end = pts[len(pts) - 1]

    angle = 15
    v = vector_mul_s(vector_sub(start, end), 0.3)

    left_side = vector_add(vector_rotate(v, angle), end)
    right_side = vector_add(vector_rotate(v, -angle), end)

    root.add(dwg.polyline(points=pts,
                          stroke=style['pen'],
                          stroke_width=width,
                          fill='none',
                          opacity=style['opaque']))

    root.add(dwg.polygon(points=[right_side, end, left_side],
                         stroke=style['pen'],
                         stroke_width=width,
                         fill=style['pen'],
                         opacity=style['opaque']))


def __vec_cmd_ellipse(dwg, root, text, style):
    pts = as_point_list(text)
    __update_bounding_box(pts, style)
    delta = vector_mul_s(vector_sub(pts[1], pts[0]), 0.5)
    root.add(dwg.ellipse(center=vector_add(pts[0], delta),
                         r=delta,
                         stroke=style['pen'],
                         stroke_width=1,
                         fill=style['brush'],
                         opacity=style['opaque']))


def __vec_cmd_railway(dwg, root, text, style):
    lst = as_list(text)
    w1 = lst[0]
    w2 = lst[1]
    h1 = lst[2]

    pts = as_points(lst[3:])
    __update_bounding_box(pts, style)

    for i in range(0, len(pts) - 1):
        start = pts[i + 1]
        end = pts[i]

        v1 = vector_sub(start, end)

        step_length = int(h1)
        step_vec = vector_mul_s(v1, step_length / vector_mod(v1))
        step_count = int(vector_mod(v1)) // step_length + 1

        s1 = vector_mul_s(vector_left(v1), float(w1))
        s2 = vector_mul_s(vector_right(v1), (float(w2) - float(w1)) / 2)
        s3 = vector_mul_s(vector_left(v1), float(w1) + (float(w2) - float(w1)) / 2)

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


def __vec_cmd_empty(dwg, root, text, style):
    pass

def __update_bounding_box(points, style):
    w, h = style['size']
    angle = style['angle']
    x0, y0, x1, y1 = style['rect']

    c = (w / 2, h / 2)

    for p in points:
        x, y = vector_add(vector_rotate(vector_sub(p, c), -angle), c)
        if x < x0:
            x0 = x
        if y < y0:
            y0 = y

        if x > x1:
            x1 = x
        if y > y1:
            y1 = y

    style['rect'] = (x0, y0, x1, y1)


