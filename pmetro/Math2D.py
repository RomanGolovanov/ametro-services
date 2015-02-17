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
    inner_product = x1*x2 + y1*y2
    len1 = math.hypot(x1, y1)
    len2 = math.hypot(x2, y2)
    return math.acos(inner_product/(len1*len2))



def get_line_angle(start, end):
    """Calculate rotation angle, clock-wise"""
    x0, y0 = start
    x1, y1 = end
    return vector_angle(vector_normalize((x1 - x0, y1 - y0)))


def vector_angle(vector):
    x, y = vector
    alpha = math.acos(x)
    beta = math.acos(y)
    if beta > 0:
        return alpha
    else:
        return math.pi - alpha


def vector_normalize(vector):
    return vector_mul(vector, 1.0 / vector_len(vector))


def vector_mul(vector, scalar):
    x, y = vector
    return x * scalar, y * scalar


def vector_len(vector):
    x, y = vector
    return math.sqrt(x * x + y * y)