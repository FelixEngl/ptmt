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
from ldatranslate import LanguageHint, PyAlignedArticleProcessor, PyDictionary, \
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
        original_dictionary_path: str | PathLike | Path,
        dictionary_path: str | PathLike | Path,
        processor: PyAlignedArticleProcessorKwArgs | PyAlignedArticleProcessor,
) -> tuple[PyDictionary, LanguagePair]:
    if isinstance(processor, dict):
        processor = create_processor(**processor)

    languages = LanguagePair.create(langcodes.get(str(lang_a)), langcodes.get(str(lang_b)))

    original_dictionary_path = Path(original_dictionary_path)
    dictionary_path = Path(dictionary_path)
    if dictionary_path.exists():
        dictionary = PyDictionary.load(dictionary_path)
    else:
        dictionary = PyDictionary.load(original_dictionary_path)
        dictionary = dictionary.process_with_tokenizer(processor)
        dictionary.save(dictionary_path)

    return dictionary, languages


def make_dictionary(
        lang_a: LanguageHint | str,
        lang_b: LanguageHint | str,
        original_dictionary_path: str | PathLike | Path,
        dictionary_path: Path | PathLike | str,
        path_to_data: Path | PathLike | str,
        output_path_phrases: Path | PathLike | str | None,
        output_path: Path | PathLike | str | None,
        processor_kwargs: PyAlignedArticleProcessorKwArgs,
        tmp_folder: None | Path | PathLike | str = None,
        token_filter: TokenCountFilter | None = None,
) -> PyDictionary:
    if not isinstance(dictionary_path, Path):
        dictionary_path = Path(dictionary_path)
    if not dictionary_path.exists():
        print(f"Create dict at: {dictionary_path}")
        dictionary, _ = create_dictionary(
            lang_a,
            lang_b,
            original_dictionary_path,
            dictionary_path,
            processor_kwargs,
            # *dictionary_sources
        )
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
