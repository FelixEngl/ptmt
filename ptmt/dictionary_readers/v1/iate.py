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

import itertools
from dataclasses import dataclass
from enum import Enum
from pprint import saferepr
from typing import Iterator, Dict, List, Optional, Tuple

from ptmt.dictionary_readers.v1.language import LanguagePair
from ptmt.dictionary_readers.v1.entries import DictionaryEntryComplete, DictionaryEntrySlim
from ptmt.dictionary_readers.v1.error_handling import ErrorConsumer
from ptmt.dictionary_readers.v1.tools import read_file_as_xml
from ptmt.toolkit.paths import str_to_path, PathObj


class ETermType(Enum):
    Term = 'fullForm'
    Abbreviation = 'abbreviation'
    Appellation = 'appellation'
    ShortForm = 'shortForm'
    Phrase = 'phrase'
    Formula = 'formula'
    Lookup = 'variant'


class ETermAdministrativeStatus(Enum):
    Preferred = 'preferredTerm-admn-sts'
    Admitted = 'admittedTerm-admn-sts'
    Deprecated = 'deprecatedTerm-admn-sts'
    Obsolete = 'supersededTerm-admn-sts'
    Proposed = 'proposedTerm-admn-sts'


@dataclass
class IATEVocabularyEntry:
    term: str
    term_type: Optional[ETermType] = None
    reliability: Optional[int] = None
    administrative_status: Optional[ETermAdministrativeStatus] = None
    indep_sub_domain: Optional[str] = None

    """
    Args:
        :param term
            The term
        :param term_type
            see ETermType
        :param reliability:
            Reliability not verified: 1
            Minimum reliability: 6
            Reliable: 9
            Very reliable: 10
        :param administrative_status
            see ETermAdministrativeStatus
        :param indep_sub_domain
            sub domains of the entry
    """


@dataclass
class EntriesWithSubDomain:
    entry_id: int
    subdomain: Optional[str]
    entries: Dict[str, List[IATEVocabularyEntry]]
    """
    Args:
        :param entry_id
            the id of the entry
        :param subdomain
            a descriptor for the subdomain of the term
        :param entries
            A dictionary mapping a language-id to a list of IATEVocabularyEntry
    """

    def __str__(self):
        return f'entry_id: {self.entry_id}\nsubdomain: {self.subdomain}\nEntries:{saferepr(self.entries)}'

    def has_needed_lang_ids(self, *lang_ids: str) -> bool:
        return all(lang_id in self.entries for lang_id in lang_ids)

    def lang_ids(self) -> Tuple[str, ...]:
        return tuple(self.entries.keys())


class LanguageNotAllowedException(Exception):
    pass


@str_to_path
def read_iate_tbx(file: PathObj) -> Iterator[EntriesWithSubDomain]:
    indep_sub_domain: Optional[str] = None
    indep_lang_cache: Dict[str, List[IATEVocabularyEntry]] = {}

    def indep_init(entry_id: str):
        nonlocal indep_sub_domain, indep_lang_cache
        entry = EntriesWithSubDomain(int(entry_id), indep_sub_domain, indep_lang_cache)
        indep_reset()
        return entry

    def indep_reset():
        nonlocal indep_sub_domain, indep_lang_cache
        indep_sub_domain = None
        indep_lang_cache = {}

    language_voc_cache: List[IATEVocabularyEntry] = []

    def language_add(lang_id: str):
        nonlocal indep_lang_cache
        if lang_id in indep_lang_cache:
            raise LanguageNotAllowedException(f"The language {lang_id} shouldn't be in the cache!")
        indep_lang_cache[lang_id] = language_voc_cache
        language_reset()

    def language_reset():
        nonlocal language_voc_cache
        language_voc_cache = []

    term_term: Optional[str] = None
    term_term_type: Optional[ETermType] = None
    term_reliability: Optional[int] = None
    term_administrative_status: Optional[ETermAdministrativeStatus] = None

    def term_add():
        nonlocal language_voc_cache
        language_voc_cache.append(term_init())
        term_reset()

    def term_reset():
        nonlocal term_term, term_term_type, term_reliability, term_administrative_status
        term_term = None
        term_term_type = None
        term_reliability = None
        term_administrative_status = None

    def term_init() -> IATEVocabularyEntry:
        nonlocal term_term, term_term_type, term_reliability, term_administrative_status, indep_sub_domain
        return IATEVocabularyEntry(term_term,
                                   term_term_type,
                                   term_reliability,
                                   term_administrative_status,
                                   indep_sub_domain)

    for data in read_file_as_xml(file):
        if data.qname == 'conceptEntry':
            yield indep_init(data.element.attrib['id'])
        elif data.qname == 'descrip':
            describ_type = data.element.attrib['type']
            if describ_type == 'subjectField':
                indep_sub_domain = data.element.text
            elif describ_type == 'reliabilityCode':
                term_reliability = int(data.element.text)
        elif data.qname == 'langSec':
            language_add(data.element.attrib['{http://www.w3.org/XML/1998/namespace}lang'])
        elif data.qname == 'termSec':
            term_add()
        elif data.qname == 'term':
            term_term = data.element.text
        elif data.qname == 'termNote':
            term_note_type = data.element.attrib['type']
            if term_note_type == 'termType':
                term_term_type = ETermType(data.element.text)
            elif term_note_type == 'administrativeStatus':
                term_administrative_status = ETermAdministrativeStatus(data.element.text)


class LanguageMissingException(Exception):
    pass


class MissingLanguageWasAlreadyEncountered(Exception):
    pass


def read_iate_dict(
        languages: LanguagePair,
        file: PathObj,
        *,
        suppress_error_print: bool = False
) -> Iterator[DictionaryEntrySlim]:
    errors = ErrorConsumer()
    encountered_errors = set()
    for i, iate_entry in enumerate(read_iate_tbx(file)):
        try:
            if not iate_entry.has_needed_lang_ids(languages.langA.language, languages.langB.language):
                len_tmp = len(encountered_errors)
                encountered_errors.add(iate_entry.entry_id)
                if len_tmp == len(encountered_errors):
                    raise MissingLanguageWasAlreadyEncountered(
                        f'The entry with {iate_entry.entry_id} misses an language, but was already encountered!'
                    )
                else:
                    raise LanguageMissingException(
                        f'The entry with {iate_entry.entry_id} misses an language!'
                    )
            entries_lang_a: list[IATEVocabularyEntry] = iate_entry.entries[languages.langA.language]
            entries_lang_b: list[IATEVocabularyEntry] = iate_entry.entries[languages.langB.language]
            for lang_a, lang_b in itertools.product(entries_lang_a, entries_lang_b):
                lang_a: IATEVocabularyEntry
                lang_b: IATEVocabularyEntry
                yield DictionaryEntryComplete(
                    lang_a.term,
                    lang_b.term,
                    langA_meta=lang_a.indep_sub_domain,
                    langB_meta=lang_b.indep_sub_domain
                )
        except Exception:
            errors.register(str(iate_entry), i+1)

    errors.to_console_classic(suppress_error_print)

