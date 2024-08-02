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

from abc import ABC
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Iterator, Tuple, Any
from lxml.etree import ElementBase as Element, QName
import lxml.etree as ET


class CharacterType(Enum):
    CHARACTER = auto()
    DIGIT = auto()
    BRACKET = auto()
    PUNCTUATION_MARK = auto()
    SPACE = auto()
    GLYPH = auto()
    UNKNOWN = auto()


def parse_string(s: str) -> Iterator[Tuple[CharacterType, str]]:
    for c in s:
        o = ord(c)
        character_type = CharacterType.UNKNOWN
        if o == 32:
            character_type = CharacterType.SPACE
        elif o in [40, 41, 60, 62, 91, 93, 123, 125]:
            character_type = CharacterType.BRACKET
        elif o in [124, 92, 47]:
            character_type = CharacterType.GLYPH
        elif o in range(65, 91) or o in range(97, 123) or c in 'äüöÄÜÖ':
            character_type = CharacterType.CHARACTER
        elif o in range(48, 58):
            character_type = CharacterType.DIGIT
        elif o in [44, 58, 59, 46, 33, 63]:
            character_type = CharacterType.PUNCTUATION_MARK
        yield character_type, c


@dataclass
class TaggedElement:
    event: str
    element: Element
    qname: str


class XMLTransformer(ABC):
    def process(self, iterator: Iterator[TaggedElement]):
        for elem in iterator:
            self._call_by_element(elem)

    def _call_by_element(self, elem: TaggedElement):
        """
        'start' and 'end', ``element`` is the Element that the parser just
        found opening or closing.  For 'start-ns', it is a tuple (prefix, URI) of
        a new namespace declaration.  For 'end-ns'
        :param elem:
        :return:
        """
        try:
            if elem.event == 'end':
                fkt = getattr(self, f'{elem.qname}_end')
            elif elem.event == 'start':
                fkt = getattr(self, f'{elem.qname}_end')
            else:
                raise ValueError(f'The event {elem.event} is not known.')
        except AttributeError:
            fkt = getattr(self, elem.qname)
        fkt(elem)


def read_file_as_xml(file: Path,
                     *events: str,
                     encoding: Any = 'UTF-8') -> Iterator[TaggedElement]:
    """
    :param file:
    :param encoding:
    :param events: 'start', 'end', 'start-ns', 'end-ns'
    :return:
    """
    if len(events) == 0:
        events = None
    for event, element in ET.iterparse(str(file.absolute()), encoding=encoding, events=events):
        element: Element
        qname = QName(element.tag).localname
        yield TaggedElement(event, element, qname)
        element.clear()
