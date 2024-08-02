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

import sys
import traceback
from itertools import groupby
from types import TracebackType
from typing import Protocol, Any, TypeVar, Tuple, Type, Collection, Iterator, List, Optional

from ptmt.toolkit.consolecolors import print_fail


class SupportedEntryType(Protocol):
    def __lt__(self, other: Any) -> bool:
        ...

    def __str__(self) -> str:
        ...


SupportedEntryTypeT = TypeVar("SupportedEntryTypeT", bound=SupportedEntryType)
_ExtInfo = Tuple[Type[BaseException], BaseException, TracebackType]
ErrorEntry = Tuple[SupportedEntryTypeT, int, Type[BaseException], BaseException, TracebackType]


def create_error_entry(entry: SupportedEntryTypeT, position: int, ext_info: _ExtInfo | None = None) -> ErrorEntry:
    if ext_info is None:
        ext_info = sys.exc_info()
    # noinspection PyTypeChecker
    return (entry, position) + ext_info


def print_error_collection(error_collection: Collection[ErrorEntry], suppress_error_print: bool = False):
    if len(error_collection) > 0:
        print_fail('##########EXCEPTIONS##########')
        print_fail(f'Had {len(error_collection)} Exceptions')
        print_fail('Statistics:')
        col = {}

        def name_getter(entry):
            return entry[3].__class__.__name__

        def line_getter(entry):
            return entry[1]

        for group_name, contents in groupby(sorted(error_collection, key=name_getter), name_getter):
            col[group_name] = tuple(sorted(contents, key=line_getter))
        for k, v in col.items():
            print_fail(f'    {k}: {len(v)}')
        if not suppress_error_print:
            print_fail("##############################")
            for exception_name, entries in col.items():
                print_fail(f'<<<<<START::{exception_name}>>>>>')
                for line, line_no, etype, value, tb in entries:
                    print_fail(f'Encountered {exception_name} at Line {line_no}')
                    print_fail(line)
                    traceback.print_exception(etype, value, tb, limit=None, file=sys.stdout, chain=True)
                    print_fail('-' * 20)
                print_fail(f'<<<<<END::{exception_name}>>>>>')
        print_fail('##############################')


class ErrorConsumer(Collection[ErrorEntry]):

    def __init__(self):
        self._backend: List[ErrorEntry] = []
        self._position_counter = 0

    def __len__(self) -> int:
        return len(self._backend)

    def __iter__(self) -> Iterator[ErrorEntry]:
        return iter(self._backend)

    def __contains__(self, __x: object) -> bool:
        return __x in self._backend

    def _generate_position(self) -> int:
        tmp = self._position_counter
        self._position_counter += 1
        return tmp

    def register(self, entry: SupportedEntryTypeT, position: Optional[int] = None, ext_info: Optional[_ExtInfo] = None):
        if position is None:
            position = self._generate_position()
        self._backend.append(create_error_entry(entry, position, ext_info))

    def to_console_classic(self, suppress_error_print: bool = False):
        print_error_collection(self, suppress_error_print=suppress_error_print)

