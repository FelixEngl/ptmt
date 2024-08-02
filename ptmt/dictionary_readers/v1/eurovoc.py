# Copyright 2024 Felix Engl
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, Dict, Callable, TypeVar, Type, Generic, Any, Tuple, Union

from ptmt.dictionary_readers.v1.language import LanguagePair
from ptmt.toolkit.paths import PathObj, str_to_path
from ptmt.dictionary_readers.v1.entries import DictionaryEntry, DictionaryEntrySlim
from ptmt.dictionary_readers.v1.readers.default_impl import DictEntryReaderIgnoreInfo
from ptmt.dictionary_readers.v1.tools import TaggedElement, read_file_as_xml


T = TypeVar('T')


class GenericRecordReadEuroVoc(Generic[T]):

    def __init__(self, creator: Type[T], definition: Dict[str, str]):
        self._definition: Dict[str, str] = definition
        self._creator: Type[T] = creator

    def __call__(self, file: Path) -> Iterator[T]:
        result_cache = {}
        for element in read_file_as_xml(file):
            element: TaggedElement
            if element.qname == 'RECORD':
                yield self._creator(**result_cache)
                result_cache = {}
            elif element.qname in self._definition:
                result_cache[self._definition[element.qname]] = element.element.text.strip()


@dataclass
class DefinitionRecord:
    descripteur_id: str
    libelle: str
    definition: Optional[str] = None


read_desc = GenericRecordReadEuroVoc(
    DefinitionRecord,
    {
        'DESCRIPTEUR_ID': 'descripteur_id',
        'LIBELLE': 'libelle',
        'DEF': 'definition'
    })


@dataclass
class DomainRecord:
    domaine_id: str
    libelle: str


read_domain = GenericRecordReadEuroVoc(
    DomainRecord,
    {
        'DOMAINE_ID': 'domaine_id',
        'LIBELLE': 'libelle'
    }
)


@dataclass
class ScopeNote:
    descripteur_id: str
    sn: Optional[str] = None
    hm: Optional[str] = None


read_scope_note = GenericRecordReadEuroVoc(
    ScopeNote,
    {
        'DESCRIPTEUR_ID': 'descripteur_id',
        'SN': 'sn',
        'HM': 'hm'
    }
)


@dataclass
class ThesaurusRecord:
    thesaurus_id: str
    libelle: str


read_thesaurus = GenericRecordReadEuroVoc(
    ThesaurusRecord,
    {
        'THESAURUS_ID': 'thesaurus_id',
        'LIBELLE': 'libelle'
    }
)


def _merge(de: Iterator[T],
           en: Iterator[T],
           id_getter: Union[Callable[[T], Any], str]) -> Iterator[Tuple[T, T]]:
    if isinstance(id_getter, str):
        copy = id_getter
        id_getter = lambda x: getattr(x, copy)
    cache_en = dict((id_getter(x), x) for x in en)
    visited = set()
    for x in de:
        de_id = id_getter(x)
        if de_id in visited:
            raise ValueError('This was already visited!')
        if de_id not in cache_en:
            raise ValueError(f'Not in the cache_en: <{x}>')
        visited.add(de_id)
        yield x, cache_en[de_id]


def _read_and_merge(
        de_file: Path,
        en_file: Path,
        extractor: GenericRecordReadEuroVoc[T],
        id_getter: Union[Callable[[T], Any], str]
) -> Iterator[Tuple[T, T]]:
    return _merge(
        extractor(de_file),
        extractor(en_file),
        id_getter
    )


def _read_eurovoc_dict(languages: LanguagePair, file: Path) -> Iterator[DictionaryEntrySlim]:
    lang_a_desc = file / f'desc_{languages.langA.language}.xml'
    lang_b_desc = file / f'desc_{languages.langB.language}.xml'
    lang_a_dom = file / f'dom_{languages.langA.language}.xml'
    lang_b_dom = file / f'dom_{languages.langB.language}.xml'
    # de_scope_note = file / 'sn_de.xml'
    # en_scope_note = file / 'sn_en.xml'
    lang_a_thesaurus = file / f'thes_{languages.langA.language}.xml'
    lang_b_thesaurus = file / f'thes_{languages.langB.language}.xml'

    for lang_a, lang_b in _read_and_merge(lang_a_desc, lang_b_desc, read_desc, 'descripteur_id'):
        yield DictionaryEntrySlim(lang_a.libelle, lang_b.libelle)

    for lang_a, lang_b in _read_and_merge(lang_a_dom, lang_b_dom, read_domain, 'domaine_id'):
        yield DictionaryEntrySlim(lang_a.libelle, lang_b.libelle)

    for lang_a, lang_b in _read_and_merge(lang_a_thesaurus, lang_b_thesaurus, read_thesaurus, 'thesaurus_id'):
        yield DictionaryEntrySlim(lang_a.libelle, lang_b.libelle)


@str_to_path
def read_eurovoc_dict(languages: LanguagePair, file: PathObj, *, suppress_error_print: bool = False) -> Iterator[DictionaryEntry]:
    return DictEntryReaderIgnoreInfo().parse_entries(_read_eurovoc_dict(languages, file),
                                                     suppress_error_print=suppress_error_print)
