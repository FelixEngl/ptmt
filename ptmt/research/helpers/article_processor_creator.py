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

from typing import TypedDict

from ldatranslate import PyVocabulary, PyAlignedArticleProcessor, PyTokenizerBuilder, PyStemmingAlgorithm

from ptmt.toolkit.stopwords import get_stop_words


class PyAlignedArticleProcessorKwArgs(TypedDict, total=False):
    lang_a: str
    lang_b: str
    stopwords_a: set[str] | str
    stopwords_b: set[str] | str
    stemmer_a: PyStemmingAlgorithm
    stemmer_b: PyStemmingAlgorithm
    phrases_a: PyVocabulary
    phrases_b: PyVocabulary


def configure_single(
    separators: list[str],
    unicode_segmentation: bool,
    stopwords_a: set[str] | str | None,
    stemmer_a: PyStemmingAlgorithm | None,
    phrases_a: PyVocabulary | None = None,
) -> PyTokenizerBuilder:
    a = PyTokenizerBuilder()
    if stopwords_a:
        a = a.stop_words(stopwords_a)
    if stemmer_a is not None:
        a = a.stemmer(stemmer_a)
    a = a.separators(separators).unicode_segmentation(unicode_segmentation)
    if phrases_a is not None:
        a = a.phrase_vocabulary(phrases_a)
    return a


def create_processor(
        lang_a: str,
        lang_b: str,
        stopwords_a: set[str] | str | None = None,
        stopwords_b: set[str] | str | None = None,
        stemmer_a: PyStemmingAlgorithm | None = None,
        stemmer_b: PyStemmingAlgorithm | None = None,
        phrases_a: PyVocabulary | None = None,
        phrases_b: PyVocabulary | None = None
) -> PyAlignedArticleProcessor:

    if isinstance(stopwords_a, str):
        stopwords_a = get_stop_words(stopwords_a)
    if isinstance(stopwords_b, str):
        stopwords_b = get_stop_words(stopwords_b)

    """Create the processor"""
    separators = [" ", ",", ":", ".", "\n", "\r\n", "(", "[", "{",
                  ")", "]", "}", "!", "\t", "?", "\"", "'",
                  "|", "`", "-", "_"]
    a = configure_single(
        separators,
        True,
        stopwords_a,
        stemmer_a,
        phrases_a,
    )

    b = configure_single(
        separators,
        True,
        stopwords_b,
        stemmer_b,
        phrases_b,
    )

    return PyAlignedArticleProcessor(
        {
            lang_a: a,
            lang_b: b,
        }
    )

