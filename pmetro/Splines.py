

def cubic_interpolate(pts):

    steps = 8
    count = len(pts) - 1
    coord = [0] * ((count * steps + 1) * 2)

    for i in range(0, count+1):
        coord[2 * i * steps] = float(pts[i][0])
        coord[2 * i * steps + 1] = float(pts[i][1])

    step = steps
    while step > 1:
        coord[step]     = (3*coord[0] + 6*coord[2 * step]     - coord[4 * step]) / 8.0
        coord[step + 1] = (3*coord[1] + 6*coord[2 * step + 1] - coord[4 * step + 1]) / 8.0

        coord[2 * count * steps - step]     = (3*coord[2 * count * steps]   + 6*coord[2 * count * steps-(2 * step)]     - coord[2 * count * steps-4 * step]) / 8.0
        coord[2 * count * steps - step + 1] = (3*coord[2 * count * steps+1] + 6*coord[2 * count * steps-(2 * step) + 1] - coord[2 * count * steps-(4 * step) + 1]) / 8.0

        for i in range(1, count * steps // step - 1):
            coord[2 * i * step + step]     = (0 - coord[2 * i * step - 2 * step]     + coord[2 * i * step] * 9     + coord[2 * i * step + 2 * step]     * 9 - coord[2 * i * step + 4 * step]    ) / 16.0
            coord[2 * i * step + step + 1] = (0 - coord[2 * i * step - 2 * step + 1] + coord[2 * i * step + 1] * 9 + coord[2 * i * step + 2 * step + 1] * 9 - coord[2 * i * step + 4 * step + 1]) / 16.0

        step //= 2

    r = []
    for i in range(0, count * steps + 1):
        r.append((coord[i*2],coord[i*2+1]))

    return r
