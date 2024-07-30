import itertools
from typing import Iterator, Tuple

from ptmt.toolkit.paths import str_to_path, PathObj
from ptmt.dictionary_readers.v1.entries import DictionaryEntrySlim
from ptmt.dictionary_readers.v1.tools import read_file_as_xml


@str_to_path
def read_pseudo_tbx(file: PathObj) -> Iterator[Tuple[str, str]]:
    lang_1_visited = False
    lang_1_cache = None

    for data in read_file_as_xml(file):
        if data.qname == 'langSet':
            lang_1_visited = data.element.attrib['{http://www.w3.org/XML/1998/namespace}lang'] == 'L1'
        elif data.qname == 'term':
            if lang_1_visited:
                yield lang_1_cache, data.element.text
                lang_1_cache = None
            else:
                if lang_1_cache is not None:
                    raise ValueError('The value of lang_1_cache should be None.')
                lang_1_cache = data.element.text


def convert_pseudo_tbx_entries_in_dict_entries(lang_a: str, lang_b: str) -> Iterator[DictionaryEntrySlim]:
    for lang_b, lang_a in itertools.product(lang_a.strip().split(';'), lang_b.strip().split(';')):
        yield DictionaryEntrySlim(lang_a.strip(), lang_b.strip())


@str_to_path
def read_dicts_info_tbx(file: PathObj) -> Iterator[DictionaryEntrySlim]:
    return itertools.chain.from_iterable(
        map(lambda en_de: convert_pseudo_tbx_entries_in_dict_entries(*en_de),
            read_pseudo_tbx(file)))


if __name__ == '__main__':
    for x in read_dicts_info_tbx(r'./../data/dicts.info/english-german-2020-12-10.tbx'):
        print(x)
