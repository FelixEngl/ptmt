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

from ldatranslate.ldatranslate import PyToken, PyTokenKind, PyAlignedArticleProcessor, LanguageHint

from ptmt.research.tmt1.toolkit.codepoint_filter import is_illegal_char

def _o_token_2_result(o_token: list[tuple[str, PyToken]]) -> tuple[str, str] | None:
    origin_word_reconstructed, processed_word_reconstructed = "", ""
    for origin, token in o_token:
        if token.kind == PyTokenKind.SeparatorSoft or token.kind == PyTokenKind.SeparatorHard or token.kind == PyTokenKind.StopWord:
            continue
        if is_illegal_char(origin) or is_illegal_char(token.lemma):
            continue
        if len(origin_word_reconstructed) > 0 and origin_word_reconstructed[-1] != " ":
            origin_word_reconstructed += " "
        if len(processed_word_reconstructed) > 0 and processed_word_reconstructed[-1] != " ":
            processed_word_reconstructed += " "
        origin_word_reconstructed += origin
        processed_word_reconstructed += token.lemma
    origin_word_reconstructed = origin_word_reconstructed.strip()
    processed_word_reconstructed = processed_word_reconstructed.strip()
    if len(origin_word_reconstructed) == 0 or len(processed_word_reconstructed) == 0:
        return None
    return origin_word_reconstructed, processed_word_reconstructed


def _process_token_list(result: list[tuple[str, PyToken]] | None, check_kind: bool = True) -> tuple[str, str, list[tuple[str, PyToken]]] | None:
    if result is None:
        return None
    if len(result) == 1 and check_kind:
        kind = result[0][1].kind
        if kind == PyTokenKind.StopWord or kind == PyTokenKind.SeparatorHard or kind == PyTokenKind.SeparatorSoft:
            return None
        if is_illegal_char(result[0][0]) or is_illegal_char(result[0][1].lemma):
            return None
    r_b = _o_token_2_result(result)
    if r_b is None:
        return None
    lang_origin, lang_processed = r_b
    return lang_origin, lang_processed, result

def _process_element(processor: PyAlignedArticleProcessor, element: str, lang: LanguageHint | str) -> tuple[str, str, list[tuple[str, PyToken]]] | None:
    result: list[tuple[str, PyToken]] | None = processor.process_string(
        lang,
        element
    )
    return _process_token_list(result)
