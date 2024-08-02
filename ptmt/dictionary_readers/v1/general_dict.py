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

from pathlib import Path
from typing import Iterator

from ptmt.dictionary_readers.v1.entries import DictionaryEntry
from ptmt.toolkit.paths import str_to_path, PathObj
from ptmt.dictionary_readers.v1.readers.dicts import ParserParam, DictReaderBase
from ptmt.dictionary_readers.v1.readers.default_impl import DictReader, DictReaderIgnoreInfo, DictEntryReaderIgnoreInfo
from ptmt.dictionary_readers.v1.readers.protocols import DictReaderCreatorParam


def _default_dict_reader_factory(parser: ParserParam, column_lang_a: int, column_lang_b: int) -> DictReaderBase:
    return DictReader(column_lang_a, column_lang_b, parser)


def ignore_info_dict_reader_factory(parser: ParserParam, column_lang_a: int, column_lang_b: int) -> DictReaderBase:
    return DictReaderIgnoreInfo(column_lang_a, column_lang_b, parser)


def ignore_info_dict_entry_reader_factory(parser: ParserParam, **kwargs) -> DictReaderBase:
    return DictEntryReaderIgnoreInfo(parser)


@str_to_path
def read_dict_file_with_parser(file: PathObj, parser: ParserParam = None, *, column_lang_a: int = 0,
                               column_lang_b: int = 1, suppress_error_print: bool = False,
                               dict_reader_factory: None | DictReaderCreatorParam = None) -> Iterator[DictionaryEntry]:
    if dict_reader_factory is None:
        dict_reader_factory = _default_dict_reader_factory
    if not isinstance(file, Path):
        file = Path(file)
    assert file.exists(), f'{file} does not exist!'
    dictionary_reader = dict_reader_factory(parser, column_lang_b=column_lang_b, column_lang_a=column_lang_a)
    with file.open('r', encoding='UTF-8') as f:
        return dictionary_reader.parse_entries(
            f.readlines(),
            skip=lambda line: line.startswith('# '),
            suppress_error_print=suppress_error_print
        )
