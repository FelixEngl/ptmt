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

import typing
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union, Iterator, Callable
from lark import Transformer
from lark.lark import Lark

from ptmt.dictionary_readers.v1.error_handling import SupportedEntryTypeT, ErrorConsumer
from ptmt.dictionary_readers.v1.entries import DictionaryEntry
from ptmt.dictionary_readers.v1.readers.transformer import LineTransformer

ParserParam = Union[None, Path, str, Lark]


class DictReaderBase(ABC):
    def __init__(self,
                 parser: ParserParam = None,
                 *,
                 transformer: Optional[Transformer] = None,
                 **lark_options):
        """
        Args:
            parser: the parser used for the dict reader, usually created by the object itself
            transformer: the transformer used to interpret the data
            filter_empty_lines: filters empty lines when set to true
            **lark_options (object): Params for Lark
        """
        self.parser: Lark = create_parser(parser, **lark_options)
        if transformer is None:
            transformer = LineTransformer()
        self.transformer: Transformer = transformer

    def parse_entries(self,
                      unfiltered_line_wise_entries: Iterator[typing.Any | SupportedEntryTypeT | None],
                      *,
                      skip: Optional[Callable[[SupportedEntryTypeT], bool]] = None,
                      suppress_error_print: bool = False,
                      crash_when_exception: bool = False) -> Iterator[DictionaryEntry]:
        """
        :return: Returns none when this line is to be skipped
        """
        error_collection = ErrorConsumer()
        for i, entry in enumerate(unfiltered_line_wise_entries):
            try:
                if entry is None:
                    continue
                if skip is not None and skip(entry):
                    continue
                processed = self._parse_entry(entry)
                if processed is None:
                    continue
                yield from processed
            except Exception as e:
                if crash_when_exception:
                    raise e
                error_collection.register(entry, i+1)
        error_collection.to_console_classic(suppress_error_print)

    @abstractmethod
    def _parse_entry(self, entry: SupportedEntryTypeT) -> Optional[Iterator[DictionaryEntry]]:
        """
        :param entry:
        :return: Returns none when this line is to be skipped
        """
        ...


def create_parser(parser: Union[None, Path, str, Lark], **lark_options) -> Lark:
    lark_options.setdefault("parser", "lalr")
    lark_options.setdefault("propagate_positions", True)
    if parser is None or isinstance(parser, str):
        if parser is None:
            parser = "dict"
        from ptmt.dictionary_readers.v1 import lark_dir
        with open("{dir}/{name}.lark".format(dir=lark_dir, name=parser), "r", encoding="UTF-8") as f:
            # return Lark(f, propagate_positions=True)
            return Lark(grammar=f, **lark_options)
    elif isinstance(parser, Lark):
        return parser
    elif isinstance(parser, Path):
        with parser.open(mode="r", encoding="UTF-8") as f:
            # return Lark(f, propagate_positions=True)
            return Lark(grammar=f, **lark_options)
    else:
        raise ValueError(f"Not supported: {parser}")


