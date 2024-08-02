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

from typing import Optional, Iterator, Any

from lark import Transformer

from ptmt.dictionary_readers.v1.entries import DictionaryEntry
from ptmt.dictionary_readers.v1.readers.dicts import DictReaderBase, ParserParam
from ptmt.dictionary_readers.v1.readers.functions import extract_dictionary_entries, convert_to_all_recombinations
from ptmt.dictionary_readers.v1.readers.transformer import TransformedParsedLine, ColumnType, BaseInfoTokenClass


class DictReader(DictReaderBase):

    def __init__(self, column_lang_a: int, column_lang_b: int, parser: ParserParam = None, *,
                 transformer: Optional[Transformer] = None, filter_empty_lines: bool = True, **lark_options):
        """

        Args:
            column_lang_b: the index of the german column in the final result
            column_lang_a: the index of the english column in the final result
        """

        super().__init__(parser, transformer=transformer, **lark_options)
        self.column_lang_b: int = column_lang_b
        self.column_lang_a: int = column_lang_a
        self.filter_empty_lines: bool = filter_empty_lines

    def _parse_entry(self, entry: str) -> Optional[Iterator[DictionaryEntry]]:
        entry = entry.strip("\t\n\r")
        if self.filter_empty_lines and len(entry) == 0:
            return None
        result: TransformedParsedLine = self.transformer.transform(self.parser.parse(entry))
        return extract_dictionary_entries(result[self.column_lang_a], result[self.column_lang_b])


def _to_ignore_info(element: Any) -> bool:
    """

    :param element: element to check
    :return: True when the element is to be ignored
    """
    return issubclass(type(element), BaseInfoTokenClass)


class DictReaderIgnoreInfo(DictReader):
    """
    Like DictReader but ignores all elements of type BaseInfoTokenClass while building the alternatives
    """

    def _parse_entry(self, entry: str) -> Optional[Iterator[DictionaryEntry]]:
        entry = entry.strip("\t\n\r")
        if self.filter_empty_lines and len(entry) == 0:
            return None
        result: TransformedParsedLine = self.transformer.transform(self.parser.parse(entry))
        return extract_dictionary_entries(
            result[self.column_lang_a],
            result[self.column_lang_b],
            converter=lambda x: convert_to_all_recombinations(x, to_ignore=_to_ignore_info)
        )


class DictEntryReader(DictReaderBase):
    def __init__(self, parser: ParserParam = None, *, transformer: Optional[Transformer] = None,
                 **lark_options):
        """
        Args:
            parser: the parser used for the dict reader, usually created by the object itself
            transformer: the transformer used to interpret the data
            filter_empty_lines: filters empty lines when set to true
            **lark_options (object): Params for Lark
        """
        if parser is None:
            parser = 'dict_single_entry'
        super().__init__(parser, transformer=transformer, **lark_options)

    def _parse_entry(self, entry: DictionaryEntry) -> Optional[Iterator[DictionaryEntry]]:
        result_lang_a: ColumnType = self.transformer.transform(self.parser.parse(entry.langA))
        result_lang_b: ColumnType = self.transformer.transform(self.parser.parse(entry.langB))
        return extract_dictionary_entries(result_lang_a, result_lang_b)


class DictEntryReaderIgnoreInfo(DictEntryReader):
    """
    Like DictReader but ignores all elements of type BaseInfoTokenClass while building the alternatives
    """

    def _parse_entry(self, entry: DictionaryEntry) -> Optional[Iterator[DictionaryEntry]]:
        result_lang_a: ColumnType = self.transformer.transform(self.parser.parse(entry.langA))
        result_lang_b: ColumnType = self.transformer.transform(self.parser.parse(entry.langB))
        return extract_dictionary_entries(result_lang_a, result_lang_b, converter=lambda x: convert_to_all_recombinations(x,
                                                                                                                   to_ignore=_to_ignore_info))
