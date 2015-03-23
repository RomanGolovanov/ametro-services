import math


def vector_rotate(v1, degree):
    degree = math.radians(degree)
    x, y = v1
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


def vector_left(v1):
    v1n = vector_mul_s(v1, 1.0 / vector_mod(v1))
    return vector_rotate(v1n, 90)


def vector_right(v1):
    v1n = vector_mul_s(v1, 1.0 / vector_mod(v1))
    return vector_rotate(v1n, -90)


def vector_sub(v1, v2):
    x1, y1 = v1
    x2, y2 = v2
    return x1 - x2, y1 - y2


def cubic_interpolate(pts):
    if (len(pts)) < 3:
        return pts

    steps = 8
    count = len(pts) - 1
    coord = [0] * ((count * steps + 1) * 2)

    for i in range(0, count + 1):
        coord[2 * i * steps] = float(pts[i][0])
        coord[2 * i * steps + 1] = float(pts[i][1])

    step = steps
    while step > 1:
        coord[step] = (3 * coord[0] + 6 * coord[2 * step] - coord[4 * step]) / 8.0
        coord[step + 1] = (3 * coord[1] + 6 * coord[2 * step + 1] - coord[4 * step + 1]) / 8.0

        coord[2 * count * steps - step] = (3 * coord[2 * count * steps] + 6 * coord[2 * count * steps - (2 * step)] -
                                           coord[2 * count * steps - 4 * step]) / 8.0
        coord[2 * count * steps - step + 1] = (3 * coord[2 * count * steps + 1] + 6 * coord[
            2 * count * steps - (2 * step) + 1] - coord[2 * count * steps - (4 * step) + 1]) / 8.0

        for i in range(1, count * steps // step - 1):
            coord[2 * i * step + step] = (0 - coord[2 * i * step - 2 * step] + coord[2 * i * step] * 9 + coord[
                2 * i * step + 2 * step] * 9 - coord[2 * i * step + 4 * step]) / 16.0
            coord[2 * i * step + step + 1] = (0 - coord[2 * i * step - 2 * step + 1] + coord[2 * i * step + 1] * 9 +
                                              coord[2 * i * step + 2 * step + 1] * 9 - coord[
                2 * i * step + 4 * step + 1]) / 16.0

        step //= 2

    r = []
    for i in range(0, count * steps + 1):
        r.append((coord[i * 2], coord[i * 2 + 1]))

    return r