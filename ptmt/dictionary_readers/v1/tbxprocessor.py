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
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Iterator, Set, Tuple

import langcodes

from ptmt.dictionary_readers.v1.entries import DictionaryEntryComplete
from ptmt.dictionary_readers.v1.error_handling import ErrorConsumer
from ptmt.dictionary_readers.v1.tools import read_file_as_xml
from ptmt.toolkit.paths import str_to_path, PathObj
from ptmt.dictionary_readers.v1.language import LanguagePair


@dataclass
class TermNote:
    term_note: str = None
    term_note_type: str = None


@dataclass
class Term:
    term_id: int
    term: str


@dataclass
class TermGroup:
    term: Term
    noted: List[TermNote]


@dataclass
class Describ:
    descrip_type: str
    describ_text: str


@dataclass
class Ntig:
    describ: List[Describ]
    term_group: TermGroup

    @property
    def term(self) -> Term:
        return self.term_group.term


@dataclass
class TermEntry:
    entry_term_id: str
    entry_content: Dict[langcodes.Language, List[Ntig]]


@str_to_path
def read_ms_tbx(file: PathObj) -> Iterator[TermEntry]:

    entry_content = {}

    def entry_reset():
        nonlocal entry_content
        entry_content = {}

    def term_entry_creation(entry_term_id: str):
        nonlocal entry_content
        tmp = TermEntry(entry_term_id, entry_content)
        entry_reset()
        return tmp

    def lang_add(lang_id: str):
        nonlocal ntig_collection, entry_content
        entry_content[langcodes.get(lang_id)] = ntig_collection
        ntig_reset()

    ntig_collection = []

    def ntig_add():
        nonlocal ntig_collection, descrip, term_group
        ntig_collection.append(Ntig(descrip, term_group))
        descrip_reset()
        term_group_reset()

    def ntig_reset():
        nonlocal ntig_collection
        ntig_collection = []

    descrip = []

    def descrip_reset():
        nonlocal descrip
        descrip = []

    def describ_add(descrip_type: str, describ_text: str):
        nonlocal descrip
        descrip.append(Describ(descrip_type, describ_text))

    term_group = None

    def term_group_create():
        nonlocal term, term_notes, term_group
        if term_group is not None:
            raise ValueError(f'term_group is not in reset-state! {term}')
        term_group = TermGroup(term, term_notes)
        term_reset()

    def term_group_reset():
        nonlocal term_group
        term_group = None

    term = None
    term_notes = []

    def term_reset():
        nonlocal term, term_notes
        term = None
        term_notes = []

    def add_term(_term_id: str, _term: str):
        nonlocal term
        if term is not None:
            raise ValueError(f'term is not in reset-state! {_term_id} - {_term}')
        term = Term(int(_term_id), _term)

    def add_term_note(term_note_type: str, term_note: str):
        nonlocal term_notes
        term_notes.append(TermNote(term_note_type, term_note))

    unknown_tag_set = set()

    def is_unknown(tag) -> bool:
        nonlocal unknown_tag_set
        is_not_known = tag not in unknown_tag_set
        if is_not_known:
            unknown_tag_set.add(tag)
        return is_not_known

    for data in read_file_as_xml(file):
        if data.qname == 'termEntry':
            yield term_entry_creation(data.element.attrib['id'])
        elif data.qname == 'langSet':
            lang_add(data.element.attrib['{http://www.w3.org/XML/1998/namespace}lang'])
        elif data.qname == 'descripGrp':
            pass
        elif data.qname == 'descrip':
            describ_add(data.element.attrib['type'], data.element.text)
        elif data.qname == 'ntig':
            ntig_add()
        elif data.qname == 'termGrp':
            term_group_create()
        elif data.qname == 'term':
            add_term(data.element.attrib['id'], data.element.text)
        elif data.qname == 'termNote':
            add_term_note(data.element.attrib['type'], data.element.text)


_RetDictType = Dict[str, Dict[int, str]]


def _default_language_extractor(term_entry: TermEntry,
                                language: langcodes.Language) -> Tuple[str, _RetDictType]:
    lang_elem: dict[int, str] = dict()
    for k, entries in term_entry.entry_content.items():
        if k.language != language.language:
            continue
        if entries is None:
            continue
        for entry in entries:
            term = entry.term
            lang_elem[term.term_id] = term.term


    result_dict: _RetDictType = defaultdict(lambda: dict())

    result_dict[language.language] = lang_elem

    # for id_ in ids:
    #     extracted = extract_language(*id_)
    #     if extracted is None:
    #         continue
    #     id_res, res = extracted
    #     res_dict = result_dict[id_res]
    #     for k, v in res.items():
    #         if k not in res_dict:
    #             res_dict[k] = v
    #         else:
    #             raise ValueError(f'The id {k} is already in the result dict!')
    #     result_dict[id_res].update(res)

    return term_entry.entry_term_id, dict(result_dict)


class TermNotInMSTermCollectionException(ValueError):
    def __init__(self, term_entry_or_message: TermEntry | str):
        if isinstance(term_entry_or_message, str):
            super().__init__(term_entry_or_message)
            self.terms_message: str = term_entry_or_message
        else:
            self.terms_message: str = ", ".join(x.term.term for cont in term_entry_or_message.entry_content.values() for x in cont)
            super().__init__(
                f'The term with the id {term_entry_or_message.entry_term_id} is not supported '
                f'by the german tbx! <{self.terms_message}>'
            )


class AlreadyProcessedException(Exception):
    pass


class WrongMappingException(Exception):
    pass


def read_ms_termcollection(
        languages: LanguagePair,
        lang_a_path: Path,
        lang_b_path: Path,
        *,
        suppress_error_print: bool = False
) -> Iterator[DictionaryEntryComplete]:

    errors = ErrorConsumer()
    processed_ids: Set[str] = set()
    dict_cache: Dict[str, _RetDictType] = dict(_default_language_extractor(_lang_a, languages.langA)
                                               for _lang_a in read_ms_tbx(lang_a_path))
    for i, entry_lang_b in enumerate(read_ms_tbx(lang_b_path)):
        try:
            if entry_lang_b.entry_term_id in processed_ids:
                raise AlreadyProcessedException(f'The entry with the id {entry_lang_b.entry_term_id} was already processed!')
            if entry_lang_b.entry_term_id in dict_cache:
                processed_ids.add(entry_lang_b.entry_term_id)

                value_holder: _RetDictType = dict_cache[entry_lang_b.entry_term_id]
                _, res_dict = _default_language_extractor(entry_lang_b, languages.langB)
                res_dict: _RetDictType
                for k, v in res_dict.items():
                    to_extend = value_holder.get(k, None)
                    if to_extend is None:
                        value_holder[k] = v
                    else:
                        for k1, v1 in v.items():
                            if k1 in to_extend:
                                if to_extend[k1] != v1:
                                    raise WrongMappingException(f'The value of {k1} is wrong, it should be {to_extend[k1]}!')
                            else:
                                to_extend[k1] = v1
            else:
                raise TermNotInMSTermCollectionException(entry_lang_b)
        except TermNotInMSTermCollectionException as e:
            errors.register(e.terms_message, i + 1)
        except Exception:
            errors.register(entry_lang_b.entry_term_id, i + 1)

    for k, v in dict_cache.items():
        try:
            if languages.langA.language not in v:
                raise TermNotInMSTermCollectionException(f"{k} of {lang_a_path} has no {languages.langA.language}")
            if languages.langB.language not in v:
                raise TermNotInMSTermCollectionException(f"{k} of {lang_b_path} has no {languages.langB.language}")
        except TermNotInMSTermCollectionException as e:
            errors.register(e.terms_message)
            continue
        for _, lang_a_value in v[languages.langA.language].items():
            for _, lang_b_value in v[languages.langB.language].items():
                yield DictionaryEntryComplete(lang_a_value, lang_b_value)

    errors.to_console_classic(suppress_error_print=suppress_error_print)


def read_ms_term_dict(
        languages: LanguagePair,
        ms_term_collection_dir: Path,
        lang_a_file_name: str,
        lang_b_file_name: str,
        *,
        suppress_error_print: bool = False
) -> Iterator[DictionaryEntryComplete]:
    lang_a_path = ms_term_collection_dir/lang_a_file_name
    if not lang_a_path.exists():
        raise FileNotFoundError(f'File {lang_a_path} does not exist!')
    lang_b_path = ms_term_collection_dir/lang_b_file_name
    if not lang_b_path.exists():
        raise FileNotFoundError(f'File {lang_b_path} does not exist!')
    return read_ms_termcollection(
        languages,
        lang_a_path,
        lang_b_path,
        suppress_error_print=suppress_error_print
    )


