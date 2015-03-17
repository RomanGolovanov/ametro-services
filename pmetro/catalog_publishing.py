import os
import shutil

from PIL import Image

from pmetro.files import get_file_ext, get_file_name_without_ext, find_appropriate_file
from pmetro.model_import import import_pmz_map
from pmetro.model_serialization import store_model
from pmetro.vec2svg import convert_vec_to_svg


def convert_map(map_info, src_path, dst_path, log):
    if not os.path.isdir(dst_path):
        os.mkdir(dst_path)

    log.message("Begin processing %s" % src_path)

    map_container = import_pmz_map(src_path, map_info)
    map_info['delays'] = map_container.meta.delays
    map_info['transports'] = map_container.meta.transport_types
    __convert_resources(map_container, src_path, dst_path, log)
    store_model(map_container, dst_path)


def __convert_resources(map_container, src_path, dst_path, log):
    res_path = os.path.join(dst_path, 'res')
    if not os.path.isdir(res_path):
        os.mkdir(res_path)

    schemes_path = os.path.join(res_path, 'schemes')
    if not os.path.isdir(schemes_path):
        os.mkdir(schemes_path)
    for scheme in map_container.schemes:
        converted_images = []
        for scheme_image in scheme.images:
            if scheme_image is None:
                continue

            converted_file_path = __convert_static_file(src_path, scheme_image, schemes_path, log)
            if converted_file_path is None:
                continue

            converted_images.append(os.path.relpath(converted_file_path, dst_path).replace('\\','/'))

        scheme.images = converted_images

    images_path = os.path.join(res_path, 'stations')
    if not os.path.isdir(images_path):
        os.mkdir(images_path)

    converted_images = []
    for image in map_container.images:

        if image.image is None:
            continue

        converted_file_path = __convert_static_file(src_path, image.image, images_path, log)
        if converted_file_path is None:
            continue

        image.image = os.path.relpath(converted_file_path, dst_path).replace('\\','/')
        converted_images.append(image)

    map_container.images = converted_images


def __convert_static_file(src_path, src_name, dst_path, log):
    __FILE_CONVERTERS = {
        'vec': (convert_vec_to_svg, 'svg'),
        'bmp': (lambda src, dst, l: Image.open(src).save(dst), 'png'),
        'gif': (lambda src, dst, l: Image.open(src).save(dst), 'png'),
        'png': (lambda src, dst, l: shutil.copy(src, dst), 'png')
    }

    src_file_path = find_appropriate_file(os.path.join(src_path, src_name))

    if not os.path.isfile(src_file_path):
        log.error('Not found image file [%s]' % src_file_path)
        return None

    src_file_ext = get_file_ext(src_file_path)
    if src_file_ext in __FILE_CONVERTERS:
        new_ext = __FILE_CONVERTERS[src_file_ext][1]
        dst_file_path = os.path.join(dst_path, get_file_name_without_ext(src_name.lower()) + '.' + new_ext)
        log.debug('Convert %s' % src_file_path)
        __FILE_CONVERTERS[src_file_ext][0](src_file_path, dst_file_path, log)
    else:
        log.warning('No converters found for file %s, copy file' % src_file_path)
        dst_file_path = os.path.join(dst_path, src_name.lower())
        shutil.copy(src_file_path, dst_file_path)

    return dst_file_path


