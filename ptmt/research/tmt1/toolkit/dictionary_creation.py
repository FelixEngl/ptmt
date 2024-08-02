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


import re
from os import PathLike

import langcodes
from ldatranslate.ldatranslate import LanguageHint, PyAlignedArticleProcessor, PyDictionary, PyDictionaryEntry, \
    TokenCountFilter, StoreOptions, read_and_parse_aligned_articles_into

from ptmt.dictionary_readers.v1.buildscript import load_from_multiple_sources
from ptmt.dictionary_readers.v1.dictionaries import DictionaryReaderLike
from ptmt.research.helpers.article_processor_creator import PyAlignedArticleProcessorKwArgs, create_processor
from ptmt.research.tmt1.toolkit.simple_processing import _process_element
from ptmt.dictionary_readers.v1.dictionary_reader_declarations import *

def process_data(
        path_to_data: Path | PathLike | str,
        output_path: Path | PathLike | str,
        processor: PyAlignedArticleProcessorKwArgs | PyAlignedArticleProcessor = None,
        tmp_folder: None | Path | PathLike | str = None,
        min_tokens: TokenCountFilter | None = None,
):
    if isinstance(processor, dict):
        processor = create_processor(**processor)

    options = StoreOptions()
    options.temp_folder = tmp_folder
    options.delete_temp_files_immediately = False
    options.deflate_temp_files = False
    options.compress_result = False
    options.show_progress_after = 1_000

    result = read_and_parse_aligned_articles_into(
        path_to_data,
        output_path,
        processor,
        min_tokens,
        options,
        with_pickle=True,
    )
    print(result)


def create_dictionary(
        lang_a: LanguageHint | str,
        lang_b: LanguageHint | str,
        dictionary_path: str | PathLike | Path,
        processor: PyAlignedArticleProcessorKwArgs | PyAlignedArticleProcessor,
        *sources: DictionaryReaderLike,
) -> tuple[PyDictionary, LanguagePair]:
    if isinstance(processor, dict):
        processor = create_processor(**processor)
    dictionary = PyDictionary(lang_a, lang_b)

    languages = LanguagePair.create(langcodes.get(str(lang_a)), langcodes.get(str(lang_b)))
    ct = 0
    for element in load_from_multiple_sources(dictionary_path, languages, *sources, suppress_error_print=True,
                                              size_conversion=EDictionaryEntrySizeConversion.NONE):

        dat = _process_element(processor, element.langA, lang_a)
        if dat is None:
            continue
        lang_a_origin, lang_a_processed, result_a = dat

        dat = _process_element(processor, element.langB, lang_b)
        if dat is None:
            continue
        lang_b_origin, lang_b_processed, result_b = dat

        assert re.match(r',,|"]', lang_a_processed) is None, \
            f"The {languages.langA} word {lang_a_processed} ({lang_a_origin}) is not valid! {element}"
        assert re.match(r',,|"]', lang_b_processed) is None, \
            f"The {languages.langB} word {lang_b_processed} ({lang_b_origin}) is not valid! {element}"

        ct += 1
        entry = PyDictionaryEntry(lang_a_processed, lang_b_processed)
        if element.origin:
            entry.set_dictionary_a_value(element.origin)
            entry.set_dictionary_b_value(element.origin)
        entry.set_unstemmed_word_a(element.langA.strip(), element.origin)
        entry.set_unstemmed_word_b(element.langB.strip(), element.origin)
        entry.set_subject_a_value(languages.langA.language)
        entry.set_subject_b_value(languages.langB.language)
        dictionary.add(entry)
        if ct % 100000 == 0:
            print(f"Stored {ct} entries")

    return dictionary, languages


def make_dictionary(
        lang_a: LanguageHint | str,
        lang_b: LanguageHint | str,
        original_dictionaries_path: str | PathLike | Path,
        dictionary_path: Path | PathLike | str,
        path_to_data: Path | PathLike | str,
        output_path_phrases: Path | PathLike | str | None,
        output_path: Path | PathLike | str | None,
        processor_kwargs: PyAlignedArticleProcessorKwArgs,
        tmp_folder: None | Path | PathLike | str = None,
        token_filter: TokenCountFilter | None = None,
        dictionary_sources: tuple[DictionaryReaderLike, ...] | None = None,
) -> PyDictionary:
    if not isinstance(dictionary_path, Path):
        dictionary_path = Path(dictionary_path)
    if not dictionary_path.is_file():
        print(f"Create dict at: {dictionary_path}")
        if dictionary_sources is not None:
            dictionary, _ = create_dictionary(
                lang_a,
                lang_b,
                original_dictionaries_path,
                processor_kwargs,
                *dictionary_sources
            )
        else:
            dictionary, _ = create_dictionary(
                lang_a,
                lang_b,
                original_dictionaries_path,
                processor_kwargs,
                muse,
                wikipedia,
                omega,
                tbx,
                dict_cc,
                ding_dict,
                free_dict,
                eurovoc,
                iate,
                ms_terms,
                wiktionary,
            )

        dictionary.save(dictionary_path)
    else:
        print("Loaded dict!")
        dictionary = PyDictionary.load(dictionary_path)

    if output_path is not None and not Path(output_path).exists():
        print(f"Create data: {output_path}")
        process_data(path_to_data, output_path, create_processor(**processor_kwargs), tmp_folder, token_filter)
    else:
        print(f"Found normal data: {output_path}")

    if output_path_phrases is not None and not Path(output_path_phrases).exists():
        print(f"Create out: {output_path_phrases}")
        processor_with_phrases = create_processor(
            **processor_kwargs,
            phrases_a=dictionary.voc_a,
            phrases_b=dictionary.voc_b,
        )
        process_data(path_to_data, output_path_phrases, processor_with_phrases, tmp_folder, token_filter)
    else:
        print(f"Found phrases data: {output_path_phrases}")

    return dictionary
