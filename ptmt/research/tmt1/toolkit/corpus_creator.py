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

from os import PathLike
from pathlib import Path

import jsonpickle
from ldatranslate import TokenCountFilter
from tomotopy.utils import Corpus

from ptmt.research.dirs import DataDirectory
from ptmt.research.tmt1.toolkit.data_creator import TokenizedValue

def create_corpus(
        language: str,
        input_path: Path | PathLike | str,
        output: DataDirectory,
        token_filter: TokenCountFilter | None = None,
        corpus_language: str | None = None
) -> Corpus:
    assert language is not None
    corpus_language = corpus_language if corpus_language is not None else language
    assert corpus_language is not None, f'Language is none!'

    if (corpus := output.corpus(corpus_language)) is not None:
        print(f"Loaded Corpus for {corpus_language}")
        return corpus
    if not isinstance(input_path, Path):
        input_path = Path(input_path)

    print("Build corpus!")

    corpus = Corpus()

    with input_path.open("r", encoding="UTF-8") as inp:
        for line in inp:
            loaded: TokenizedValue = jsonpickle.loads(line)
            if len(loaded.entries) < 2:
                continue
            words = loaded.entries[language].tokenized
            if token_filter is not None and len(words) not in token_filter:
                continue
            corpus.add_doc(loaded.entries[corpus_language].tokenized)
    print(f"Save {corpus_language} to {output.corpus_path(corpus_language)}")
    corpus.save(str(output.corpus_path(corpus_language).absolute()))
    output.set_corpus(corpus_language, corpus)
    return corpus
