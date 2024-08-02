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

from collections import defaultdict
from enum import Flag, auto
import re
from dataclasses import dataclass
from pprint import pprint
from typing import Iterator

from ptmt.dictionary_readers.v1.entries import DictionaryEntry
from ptmt.toolkit.consolecolors import print_fail
from ptmt.toolkit.paths import str_to_path, PathObj


class LineElementType(Flag):
    NONE = 0x0
    CONTENT = auto()
    LANGUAGE_META = auto()
    TOPIC_META = auto()
    ADDITIONAL_META = auto()
    SPECIAL_META = auto()
    LANGUAGE_SEPARATOR = auto()
    WORD_SEPARATOR = auto()
    ALTERNATIVE_SEPARATOR = auto()
    ALTERNATIVE_RECOMBINATION_META = auto()
    ALL_SEPARATORS = LANGUAGE_SEPARATOR | WORD_SEPARATOR | ALTERNATIVE_SEPARATOR
    ALL_META = TOPIC_META | ADDITIONAL_META | LANGUAGE_META | SPECIAL_META | ALTERNATIVE_RECOMBINATION_META


@dataclass
class LineElement:
    element_type: LineElementType
    start: int
    end: int
    value: str


# _parse_regex = re.compile(r'(?<![\(\{\[])\b[^\{\[\(\)\]\}]+\b(?![\w\s]*[\)\]\}])|(?:([\{\(\[])(.*?)([\}\]\)]))')
_parse_regex = re.compile(r'(?<![\(\{\[])\b[^\{\[\(\)\]\}\|\:\;\/]+\b(?![\w\s]*[\)\]\}])|(?:\s([\{\(\[\/])([^\}\]\)\|\;\:]+)([\}\]\)\/]))|\||\:\:|\;|(\/)(\w+)')


def _parse_line(line: str) -> Iterator[LineElement]:
    if len(line.strip()) == 0:
        return None
    for entry in _parse_regex.finditer(line):
        bracket_open, value, bracket_close, alternative_marker, alternative_value = entry.groups()
        if bracket_open == '{':
            meta_type = LineElementType.LANGUAGE_META
        elif bracket_open == '[':
            meta_type = LineElementType.TOPIC_META
        elif bracket_open == '(':
            meta_type = LineElementType.ADDITIONAL_META
        elif bracket_open == '/':
            meta_type = LineElementType.SPECIAL_META
        elif alternative_marker == '/':
            meta_type = LineElementType.ALTERNATIVE_RECOMBINATION_META
            value = alternative_value
        else:
            value = entry.group(0)
            if value == '|':
                meta_type = LineElementType.WORD_SEPARATOR
            elif value == '::':
                meta_type = LineElementType.LANGUAGE_SEPARATOR
            elif value == ';':
                meta_type = LineElementType.ALTERNATIVE_SEPARATOR
            else:
                meta_type = LineElementType.CONTENT
        yield LineElement(meta_type, *entry.span(), value)


def parse_ding_line(line: str) -> Iterator[DictionaryEntry]:
    lang1 = []
    lang2 = []
    act_lang = lang1
    act_collector = None

    def new_act_collector():
        nonlocal act_collector, act_lang
        act_collector = []
        act_lang.append(act_collector)

    def flip_lang():
        nonlocal lang2, act_lang
        act_lang = lang2
        new_act_collector()

    new_act_collector()

    last_element_type = LineElementType.NONE
    encountered_end_meta_in_word = False
    elements_to_process = []
    for element in _parse_line(line):
        if element.element_type == LineElementType.CONTENT:
            if last_element_type in LineElementType.ALL_SEPARATORS or \
                    last_element_type == LineElementType.LANGUAGE_META or \
                    not encountered_end_meta_in_word or \
                    last_element_type == LineElementType.ALTERNATIVE_RECOMBINATION_META:
                elements_to_process.append(element)
            else:
                raise ValueError(f'The value <{element.element_type}> is not following a <{str(last_element_type.ALL_SEPARATORS)}> but a <{last_element_type}>.')
        elif element.element_type in LineElementType.ALL_SEPARATORS:
            if len(elements_to_process) == 1:
                act_collector.append(elements_to_process[0].value)
            else:
                no_meta = [x.value for x in elements_to_process if x.element_type != LineElementType.ADDITIONAL_META]
                if len(elements_to_process) - len(no_meta) > 1:
                    raise ValueError(f'The element has too many {LineElementType.ADDITIONAL_META} elements for a goot heuristical processing')
                act_collector.append(' '.join(x.value for x in elements_to_process))
                act_collector.append(' '.join(no_meta))
            elements_to_process.clear()
            encountered_end_meta_in_word = False
            if element.element_type == LineElementType.LANGUAGE_SEPARATOR:
                flip_lang()
            elif element.element_type == LineElementType.WORD_SEPARATOR:
                new_act_collector()
        elif element.element_type in LineElementType.ALL_META:
            if element.element_type == LineElementType.LANGUAGE_META:
                encountered_end_meta_in_word = True
            elif element.element_type == LineElementType.ADDITIONAL_META:
                if not encountered_end_meta_in_word:
                    elements_to_process.append(element)
            elif element.element_type == LineElementType.TOPIC_META:
                encountered_end_meta_in_word = True
            elif element.element_type == LineElementType.SPECIAL_META:
                encountered_end_meta_in_word = True
            elif element.element_type == LineElementType.ALTERNATIVE_RECOMBINATION_META:
                elements_to_process.append(element)
        last_element_type = element.element_type
    for ger, en in zip(lang1, lang2):
        for g in ger:
            for e in en:
                yield DictionaryEntry(g, e)


# def parse_line(line: str):
#     collection_ger = []
#     collection_en = []
#     actual_collection = collection_ger
#     s_tmp = ''
#     last_character_type = None
#     last_character = None
#     for character_type, character in parse_string(line):
#         if character_type == CharacterType.CHARACTER:
#             s_tmp += character
#         elif character_type == CharacterType.PUNCTUATION_MARK:
#             if character == ':' and last_character == ':':
#                 actual_collection = c
#
#         last_character_type = character_type
#         last_character = character

@str_to_path
def read_ding_dict(file: PathObj, *, ignore_errors: bool = True, suppress_error_print: bool = False) -> Iterator[DictionaryEntry]:
    with file.open('r', encoding='UTF-8') as f:
        error_count = 0
        error_type_count = defaultdict(lambda: 0)
        for i, line in enumerate(f.readlines()):
            try:
                if line.startswith('#'):
                    continue
                for parsed in parse_ding_line(line):
                    yield parsed
            except ValueError as v:
                error_count += 1
                error_str = str(v)
                error_type_count[error_str] += 1
                if not ignore_errors:
                    raise v
                if suppress_error_print:
                    continue
                print_fail(f'Error at line: {i}')
                print_fail(f'    {error_str}')
                print_fail(f'    {line}')
        print('#' * 30)
        print_fail(f'Error Count: {error_count}')
        pprint(error_type_count)
        print('#'*30)

