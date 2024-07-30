import itertools
import typing
from pathlib import Path
from typing import Callable

from ptmt.dictionary_readers.v1.dictionaries import as_dictionary_reader, register_dictionary_reader_args, \
    register_default_dictionary_reader_args
from ptmt.dictionary_readers.v1.dicts_info import convert_pseudo_tbx_entries_in_dict_entries, read_pseudo_tbx
from ptmt.dictionary_readers.v1.language import LanguagePair
from ptmt.dictionary_readers.v1.entries import *
from ptmt.dictionary_readers.v1.eurovoc import read_eurovoc_dict
from ptmt.dictionary_readers.v1.free_dict import lang_b_to_lang_a_mapper, lang_a_to_lang_b_mapper, \
    read_free_dict
from ptmt.dictionary_readers.v1.general_dict import ignore_info_dict_reader_factory, \
    read_dict_file_with_parser
from ptmt.dictionary_readers.v1.iate import read_iate_dict
from ptmt.dictionary_readers.v1.readers.muse import muse_impl
from ptmt.dictionary_readers.v1.tbxprocessor import read_ms_term_dict
from ptmt.toolkit.paths import PathObj


@as_dictionary_reader("MUSE", force_dictionary_reader_args=False)
def muse(direction: LanguagePair, data_path: PathObj, *_, **__) -> typing.Iterator[DictionaryEntrySlim]:
    return muse_impl(direction, data_path)


@as_dictionary_reader("dict.info-Wikipedia", force_dictionary_reader_args=False)
@register_default_dictionary_reader_args(dict_reader_factory=ignore_info_dict_reader_factory)
@register_dictionary_reader_args("en", "de", file_name='Wikipedia.txt', column_lang_a=1, column_lang_b=0)
def wikipedia(_: LanguagePair, data_path: PathObj, file_name: str, *args, **kwargs) -> typing.Iterator[DictionaryEntry]:
    if not isinstance(data_path, Path):
        data_path = Path(data_path)
    dicts_info_wikipedia = data_path / 'dicts.info' / file_name
    if not dicts_info_wikipedia.exists():
        raise FileNotFoundError(f'File {dicts_info_wikipedia} does not exist!')
    return read_dict_file_with_parser(
        dicts_info_wikipedia,
        *args,
        **kwargs
    )


@as_dictionary_reader("dict.info-OmegaWiki", force_dictionary_reader_args=False)
@register_default_dictionary_reader_args(dict_reader_factory=ignore_info_dict_reader_factory)
@register_dictionary_reader_args("en", "de", file_name="OmegaWiki.txt", column_lang_a=1, column_lang_b=0)
def omega(_: LanguagePair, data_path: PathObj, file_name: str, *args, **kwargs) -> typing.Iterator[DictionaryEntry]:
    if not isinstance(data_path, Path):
        data_path = Path(data_path)
    dicts_info_wikipedia = data_path / 'dicts.info' / file_name
    if not dicts_info_wikipedia.exists():
        raise FileNotFoundError(f'File {dicts_info_wikipedia} does not exist!')
    return read_dict_file_with_parser(
        dicts_info_wikipedia,
        *args,
        **kwargs
    )


@as_dictionary_reader("dict.info-TBX", force_dictionary_reader_args=False)
@register_dictionary_reader_args("en", "de", file_name="english-german-2020-12-10.tbx")
def tbx(_: LanguagePair, data_path: PathObj, file_name: str) -> typing.Iterator[DictionaryEntrySlim]:
    if not isinstance(data_path, Path):
        data_path = Path(data_path)
    data_path = data_path / 'dicts.info' / file_name
    if not data_path.exists():
        raise FileNotFoundError(f'File {data_path} does not exist!')
    return itertools.chain.from_iterable(
        map(lambda a_b: convert_pseudo_tbx_entries_in_dict_entries(*a_b), read_pseudo_tbx(data_path)))


@as_dictionary_reader("DictCC", force_dictionary_reader_args=False)
@register_default_dictionary_reader_args(dict_reader_factory=ignore_info_dict_reader_factory)
@register_dictionary_reader_args("en", "de", file_name="dict.txt", column_lang_a=0, column_lang_b=1)
def dict_cc(_: LanguagePair, data_path: PathObj, file_name: str, *args, **kwargs) -> typing.Iterator[DictionaryEntry]:
    if not isinstance(data_path, Path):
        data_path = Path(data_path)
    dict_cc_dict = data_path / 'DictCC' / file_name
    if not dict_cc_dict.exists():
        raise FileNotFoundError(f'File {dict_cc_dict} does not exist!')
    return read_dict_file_with_parser(
        dict_cc_dict,
        *args,
        **kwargs
    )

@as_dictionary_reader("DingDict", force_dictionary_reader_args=False)
@register_default_dictionary_reader_args(dict_reader_factory=ignore_info_dict_reader_factory)
@register_dictionary_reader_args("en", "de", file_name="de-en.txt", column_lang_a=1, column_lang_b=0)
def ding_dict(_: LanguagePair, data_path: PathObj, file_name: str, *args, **kwargs) -> typing.Iterator[DictionaryEntry]:
    if not isinstance(data_path, Path):
        data_path = Path(data_path)
    path = data_path / 'ding' / file_name
    if not path.exists():
        raise FileNotFoundError(f'File {path} does not exist!')
    return read_dict_file_with_parser(
        path,
        *args,
        **kwargs
    )

@as_dictionary_reader("FreeDict", force_dictionary_reader_args=False)
@register_dictionary_reader_args("en", "de", sub_path='en_de/eng-deu.tei', mapping=lang_a_to_lang_b_mapper)
@register_dictionary_reader_args("en", "de", sub_path='de_en/deu-eng.tei', mapping=lang_b_to_lang_a_mapper)
def free_dict(_: LanguagePair, data_path: PathObj, sub_path: str, mapping: Callable[[Tuple[str, str]], DictionaryEntrySlim], *args, **kwargs) -> typing.Iterator[DictionaryEntry]:
    if not isinstance(data_path, Path):
        data_path = Path(data_path)
    path = data_path / 'freedict' / sub_path
    if not path.exists():
        raise FileNotFoundError(f'File {path} does not exist!')
    return read_free_dict(
        path,
        mapping,
        *args,
        **kwargs
    )

@as_dictionary_reader("EuroVoc", force_dictionary_reader_args=False)
def eurovoc(languages: LanguagePair, data_path: PathObj, *args, **kwargs) -> typing.Iterator[DictionaryEntry]:
    if not isinstance(data_path, Path):
        data_path = Path(data_path)
    eurovoc_dir = data_path / 'eurovoc'
    if not eurovoc_dir.exists():
        raise FileNotFoundError(f'Directory {eurovoc_dir} does not exist!')
    return read_eurovoc_dict(
        languages,
        eurovoc_dir,
        *args,
        **kwargs
    )


@as_dictionary_reader("IATE", force_dictionary_reader_args=False)
def iate(languages: LanguagePair, data_path: PathObj, *args, **kwargs) -> typing.Iterator[DictionaryEntry]:
    if not isinstance(data_path, Path):
        data_path = Path(data_path)
    iate_dir = data_path / 'IATE' / 'IATE_export.tbx'
    if not iate_dir.exists():
        raise FileNotFoundError(f'File {iate_dir} does not exist!')
    return read_iate_dict(
        languages,
        iate_dir,
        *args,
        **kwargs
    )


@as_dictionary_reader("ms-terms", force_dictionary_reader_args=False)
@register_dictionary_reader_args("en", "de",
                                 lang_a_file_name="MicrosoftTermCollectio_british_englisch.tbx",
                                 lang_b_file_name='MicrosoftTermCollection_german.tbx')
def ms_terms(languages: LanguagePair, data_path: PathObj, lang_a_file_name: str, lang_b_file_name: str, *args, **kwargs) -> typing.Iterator[DictionaryEntry]:
    if not isinstance(data_path, Path):
        data_path = Path(data_path)
    ms_terms_dir = data_path / 'Microsoft TermCollection'
    return read_ms_term_dict(
        languages,
        ms_terms_dir,
        lang_a_file_name,
        lang_b_file_name,
        *args,
        **kwargs
    )


@as_dictionary_reader("Wiktionary", force_dictionary_reader_args=False)
@register_default_dictionary_reader_args(dict_reader_factory=ignore_info_dict_reader_factory)
@register_dictionary_reader_args("en", "de", file_name="transformed", column_lang_a=1, column_lang_b=0)
def wiktionary(_: LanguagePair, data_path: PathObj, file_name: str, *args, **kwargs) -> typing.Iterator[DictionaryEntry]:
    wiktionary_dict = data_path / 'Wiktionary' / file_name
    if not wiktionary_dict.exists():
        raise FileNotFoundError(f'File {wiktionary_dict} does not exist!')
    return read_dict_file_with_parser(wiktionary_dict, 'dict_wiki', *args, **kwargs)


if __name__ == "__main__":
    def x(a, b):
        pass

    def y(*args, **kwargs):
        x(*args, **kwargs)

    y("")
