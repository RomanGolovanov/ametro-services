import re

__RUSH_HOURS = ['08:00-10:00', '17:00-19:00']
__DAY_RANGES = ['08:00-20:00']
__NIGHT_RANGES = ['20:00-24:00', '00:00-05:00']
__EVENING_RANGES = ['19:00-24:00']
__WORK_DAYS = 'workdays'
__WEEK_END = 'weekend'

__KNOWN_DELAYS = {
    'Day': dict(type='day', ranges=__DAY_RANGES, weekdays=None),
    'День': dict(type='day', ranges=__DAY_RANGES, weekdays=None),
    'Выходной': dict(type='day', ranges=__DAY_RANGES, weekdays=__WEEK_END),
    'День (вых.)': dict(type='day', ranges=__DAY_RANGES, weekdays=__WEEK_END),
    'День (раб.)': dict(type='day', ranges=__DAY_RANGES, weekdays=__WORK_DAYS),

    'Night': dict(type='night', ranges=__NIGHT_RANGES, weekdays=None),
    'Ночь': dict(type='night', ranges=__NIGHT_RANGES, weekdays=None),

    'Вечер (вых.)': dict(type='evening', ranges=__EVENING_RANGES, weekdays=__WEEK_END),
    'Вечер (раб.)': dict(type='evening', ranges=__EVENING_RANGES, weekdays=__WORK_DAYS),
    'после 19.00': dict(type='evening', ranges=__EVENING_RANGES, weekdays=None),
    'Утро': dict(type='mourning', ranges=['05:00-08:00'], weekdays=None),

    'Час-пик': dict(type='rush', ranges=__RUSH_HOURS, weekdays=__WORK_DAYS),

    'Без пересадок': dict(type='direct', ranges=None, weekdays=None),
    'Запад-Север': dict(type='west-north', ranges=None, weekdays=None),
    'Запад-Юг': dict(type='west-south', ranges=None, weekdays=None),
    'Север-Запад': dict(type='north-west', ranges=None, weekdays=None),
    'Север-Юг': dict(type='north-south', ranges=None, weekdays=None),
    'Юг-Запад': dict(type='south-west', ranges=None, weekdays=None),
    'Юг-Север': dict(type='south-north', ranges=None, weekdays=None),
}

__KNOWN_WEEKDAYS = {
    'Пн': 'monday',
    'Вт': 'tuesday',
    'Ср': 'wednesday',
    'Чт': 'thursday',
    'Пт': 'friday',
    'Сб': 'saturday',
    'Вс': 'sunday',
    'ПнПт': __WORK_DAYS,
    'СбВс': __WEEK_END
}


def __parse_delays(lines, text_index_table):
    delays = []

    for l in lines:

        if l in __KNOWN_DELAYS:
            delays.append(__KNOWN_DELAYS[l])
            continue

        name = re.findall('[^\s]+', l)[0]

        range_match = re.findall('(?P<h1>\d{1,2})[\.:](?P<m1>\d{1,2})\s*[\s-]\s*(?P<h2>\d{1,2})[\.:](?P<m2>\d{1,2})', l)
        if len(range_match) == 1:
            if len(re.findall('\s', l)) == 0:
                name = None

            h1, m1, h2, m2 = range_match[0]
            time_range = ['{0:0>#2}:{1:0>#2}-{2:0>#2}:{3:0>#2}'.format(int(h1), int(m1), int(h2), int(m2))]
        else:
            time_range = None

        weekdays_match = re.findall('(ПнПт|СбВс|Пн|Вт|Ср|Чт|Пт|Сб|Вс)+', l)
        if len(weekdays_match) == 1 and weekdays_match[0] in __KNOWN_WEEKDAYS:
            weekdays = __KNOWN_WEEKDAYS[weekdays_match[0]]
        else:
            weekdays = None

        delays.append(dict(
            type='custom',
            name_id=text_index_table.as_text_id(name),
            ranges=time_range,
            weekdays=weekdays))

    return delays
