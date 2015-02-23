import os
from pmetro.files import get_file_ext
from pmetro.ini_files import deserialize_ini, get_ini_attr, get_ini_section
from pmetro.model_objects import MapImage


def load_static(map_container, src_path):
    txt_files = sorted([x for x in os.listdir(src_path) if get_file_ext(x) == 'txt'])

    map_container.images = []
    for txt_file in txt_files:
        ini = deserialize_ini(os.path.join(src_path, txt_file))

        txt_caption = get_ini_attr(ini, 'Options', 'Caption')
        txt_type = get_ini_attr(ini, 'Options', 'Type')
        if txt_type == 'Image':
            __load_images(map_container.images, txt_caption, ini)


def __load_images(images, caption, ini):
    for line_name in ini:
        if line_name == 'Options' or line_name.startswith('__'):
            continue
        for station_name in get_ini_section(ini, line_name):
            for image_file in str(ini[line_name][station_name]).split('\n'):
                image = MapImage()
                image.caption = caption
                image.line = line_name
                image.station = station_name
                image.image = image_file
                images.append(image)
