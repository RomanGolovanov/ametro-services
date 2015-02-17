# -*- coding: utf-8 -*-

import math

def rotate_points(src_points, degree):
    """Rotates points which consists of corners represented as (x,y), around the ORIGIN, clock-wise"""
    degree = math.radians(degree)
    points = []
    for p in src_points:
        points.append((p[0] * math.cos(degree) - p[1] * math.sin(degree),
                       p[0] * math.sin(degree) + p[1] * math.cos(degree)))
    return points


def angle(pt1, pt2):
    x1, y1 = pt1
    x2, y2 = pt2
    inner_product = x1 * x2 + y1 * y2
    len1 = math.hypot(x1, y1)
    len2 = math.hypot(x2, y2)
    return math.acos(inner_product / (len1 * len2))


def vector_angle(vector):
    x, y = vector
    alpha = math.acos(x)
    beta = math.acos(y)
    if beta > 0:
        return alpha
    else:
        return math.pi - alpha


