# -*- coding: utf-8 -*-

import math


def vector_rotate(v1, degree):
    degree = math.radians(degree)
    x,y = v1
    return x * math.cos(degree) - y * math.sin(degree), x * math.sin(degree) + y * math.cos(degree)


def vector_angle(v1, v2):
    x1, y1 = v1
    x2, y2 = v2
    inner_product = x1 * x2 + y1 * y2
    len1 = math.hypot(x1, y1)
    len2 = math.hypot(x2, y2)
    return math.acos(inner_product / (len1 * len2))


def vector_mod(vec):
    x, y = vec
    return math.sqrt(x * x + y * y)


def vector_mul_s(v1, s):
    return vector_mul(v1, (s, s))


def vector_mul(v1, v2):
    x1, y1 = v1
    x2, y2 = v2
    return x1 * x2, y1 * y2


def vector_add(v1, v2):
    x1, y1 = v1
    x2, y2 = v2
    return x1 + x2, y1 + y2


def vector_sub(v1, v2):
    x1, y1 = v1
    x2, y2 = v2
    return x1 - x2, y1 - y2