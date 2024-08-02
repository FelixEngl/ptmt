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

from typing import Iterator, Tuple, Callable

from ptmt.dictionary_readers.v1.entries import DictionaryEntrySlim, DictionaryEntry
from ptmt.dictionary_readers.v1.readers.default_impl import DictEntryReader
from ptmt.dictionary_readers.v1.tools import read_file_as_xml
from ptmt.toolkit.paths import str_to_path, PathObj


@str_to_path
def read_tei_file(file: PathObj) -> Iterator[Tuple[str, str]]:
    orths = []
    cits = []
    for data in read_file_as_xml(file):
        if data.qname == 'entry':
            for orth in orths:
                for cit in cits:
                    yield orth, cit
            cits = []
            orths = []
        elif data.qname == 'orth':
            orths.append(data.element.text)
        elif data.qname == 'quote':
            cits.append(data.element.text)


def lang_a_to_lang_b_mapper(tup: Tuple[str, str]) -> DictionaryEntrySlim:
    return DictionaryEntrySlim(tup[0], tup[1])


def lang_b_to_lang_a_mapper(tup: Tuple[str, str]) -> DictionaryEntrySlim:
    return DictionaryEntrySlim(tup[1], tup[0])


@str_to_path
def read_free_dict(file: PathObj,
                   mapper: Callable[[Tuple[str, str]], DictionaryEntrySlim],
                   *,
                   use_special_parser: bool = True,
                   suppress_error_print: bool = False) -> Iterator[DictionaryEntry]:
    if use_special_parser:
        return DictEntryReader().parse_entries(map(mapper, read_tei_file(file)),
                                               suppress_error_print=suppress_error_print)
    else:
        return map(mapper, read_tei_file(file))
