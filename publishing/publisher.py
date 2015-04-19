import codecs
import json
import os
import shutil
from pmetro.file_utils import get_file_ext


def publish_maps(maps_path, publishing_path):

    index = __build_index(maps_path)

    for file_name in [f for f in os.listdir(maps_path) if get_file_ext(os.path.join(maps_path, f)) == 'zip']:
        source_file = os.path.join(maps_path, file_name)
        destination_file = os.path.join(publishing_path, file_name)

        if os.path.isfile(destination_file):
            os.remove(destination_file)

        shutil.copy2(source_file, publishing_path)

    for locale in index['locales']:
        with codecs.open(os.path.join(publishing_path, 'index.{0}.json'.format(locale)), 'w', 'utf-8') as f:
            f.write(
                json.dumps(index['locales'][locale], ensure_ascii=False, indent=4))

    with codecs.open(os.path.join(publishing_path, 'index.json'), 'w', 'utf-8') as f:
        f.write(
            json.dumps(index['locales'][index['default_locale']], ensure_ascii=False, indent=4))

def __build_index(maps_path):
    return dict(
        locales=dict(
            en={},
            ru={},
            jp={},
            it={}
        ),
        default_locale='en'
    )


