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
from enum import Enum
from typing import Optional, Tuple
from pympler.asizeof import asizeof

from ptmt.dictionary_readers.v1.readers.linetree import LineTreeNode
from ptmt.toolkit.enums import CallableEnumValue


@dataclass
class DictionaryEntry:
    langA: str
    langB: str
    origin: Optional[str] = None

    # needed to get right annotations through inheritance
    @classmethod
    def get_annotations(cls):
        d = {}
        for c in cls.mro():
            try:
                d.update(**c.__annotations__)
            except AttributeError:
                # object, at least, has no __annotations__ attribute.
                pass
        return d


@dataclass
class DictionaryEntrySlim(DictionaryEntry):
    pass


@dataclass
class DictionaryEntryReduced(DictionaryEntrySlim):
    langA_meta: Optional[str | tuple[str, ...]] = None
    langB_meta: Optional[str | tuple[str, ...]] = None


@dataclass
class DictionaryEntryComplete(DictionaryEntryReduced):
    langA_original_tokens: Optional[Tuple[LineTreeNode, ...]] = None
    langB_original_tokens: Optional[Tuple[LineTreeNode, ...]] = None


def to_slim(entry: DictionaryEntry) -> DictionaryEntrySlim:
    if isinstance(entry, DictionaryEntrySlim):
        return entry
    return DictionaryEntrySlim(*tuple(entry.__dict__.values())[:3])


def to_reduced(entry: DictionaryEntry) -> DictionaryEntryReduced:
    if isinstance(entry, DictionaryEntryReduced):
        return entry
    return DictionaryEntryReduced(*tuple(entry.__dict__.values())[:5])


def to_complete(entry: DictionaryEntry) -> DictionaryEntryComplete:
    if isinstance(entry, DictionaryEntryComplete):
        return entry
    return DictionaryEntryComplete(*tuple(entry.__dict__.values()))


class EDictionaryEntrySizeConversion(Enum):
    SLIM = CallableEnumValue(to_slim)
    REDUCED = CallableEnumValue(to_reduced)
    COMPLETE = CallableEnumValue(to_complete)
    NONE = CallableEnumValue(lambda x: x)

    def convert(self, entry: DictionaryEntry) -> DictionaryEntry:
        return self.value(entry)


if __name__ == '__main__':
    a = DictionaryEntry('', '', ''), DictionaryEntrySlim('a_s', 'b_s', 'c_s')
    b = DictionaryEntryReduced('', '', ''), DictionaryEntryReduced('a_r', 'b_r', 'c_r', ('d_r',), ('e_r',))
    c = DictionaryEntryComplete('', '', ''), DictionaryEntryComplete('a_c', 'b_c', 'c_c', ('d_c',), ('e_c',), ('f_c',), ('g_c',))


    def test(base, used):
        print(f'Base size: {asizeof(base)}')
        print(f'Used size: {asizeof(used)}')

        print(f'Base size to_slim: {asizeof(to_slim(base))}')
        print(f'Used size to_slim: {asizeof(to_slim(used))}')

        print(f'Base size to_reduced: {asizeof(to_reduced(base))}')
        print(f'Used size to_reduced: {asizeof(to_reduced(used))}')

        print(f'Base size to_completed: {asizeof(to_complete(base))}')
        print(f'Used size to_completed: {asizeof(to_complete(used))}')

        for x in EDictionaryEntrySizeConversion:
            print(f'Base size {x}: {asizeof(x.convert(base))}')
            print(f'Used size {x}: {asizeof(x.convert(used))}')

        print()

    test(*a)
    test(*b)
    test(*c)
