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

import multiprocessing
import typing
from os import PathLike
from pathlib import Path
from typing import TypedDict, Callable

import gensim
from gensim.corpora import Dictionary
from gensim.models import CoherenceModel
from ldatranslate import PyTopicModel, TokenCountFilter

from ptmt.lda.topic_model import CoherenceModelData
from ptmt.research.dirs import DataDirectory, CoherencesDir
from ptmt.research.helpers.timer import SimpleTimer
from ptmt.research.tmt1.toolkit.corpus_creator import create_corpus


class CoherenceModelKwArgs(TypedDict, total=False):
    topics: list[list[str]]
    texts: list[list[str]]
    dictionary: Dictionary
    corpus: list[list[tuple[int, int]]]
    topn: int
    coherence: str
    window_size: int | None


def _execute_get_coherence(queue: multiprocessing.Queue, coherence_kwargs: CoherenceModelKwArgs):
    try:
        coherence = gensim.models.CoherenceModel(**coherence_kwargs)
        value = coherence.get_coherence()
        if not isinstance(value, float):
            value = float(value)
        queue.put(value)
    except Exception as e:
        queue.put(e)


class LazyPyTopicModelLoader:
    def __init__(self, loader: Callable[[], PyTopicModel]):
        self.loader = loader

    def __call__(self):
        return self.loader()


class LazyCoherenceModelData:
    def __init__(
            self,
            language: str,
            input_path: Path | PathLike | str,
            output: DataDirectory,
            token_filter: TokenCountFilter | None = None,
            corpus_language: str | None = None
    ):
        self.language = language
        self.input_path = input_path
        self.output = output
        self.token_filter = token_filter
        self.corpus_language = corpus_language
        self._coherence_data: None | CoherenceModelData = None

    def __call__(self) -> CoherenceModelData:
        if self._coherence_data is None:
            print(f"Create coherence data for {self.language} with target {self.corpus_language}")
            corpus = create_corpus(self.language, self.input_path, self.output, token_filter=self.token_filter,
                                   corpus_language=self.corpus_language)
            self._coherence_data = CoherenceModelData.create_from(corpus)
        return self._coherence_data


def calculate_and_store_coocurrence_single(
        model: PyTopicModel | LazyPyTopicModelLoader,
        coherence_dir: CoherencesDir,
        data: CoherenceModelData | LazyCoherenceModelData,
        coocurrences: typing.Iterable[str],
        topn: int = 20,
        window_size: int | None = None,
        keep_phrases: bool = False,
        timeout_for_calculation: int | None = None,
) -> dict[str, float | CoherenceModel]:
    """
    timeout_for_calculation: in minutes
    """
    print(f"Create Coherences for {coherence_dir.root_dir}")
    result = dict()

    timeout_for_calculation = 20 if timeout_for_calculation is None else timeout_for_calculation

    with SimpleTimer():
        topics: list[list[str]] | None = None
        for target in coocurrences:

            if coherence_dir.exists(target):
                print(f'  load {target}')
                result[target] = coherence_dir.load_coherence(target)
            else:
                print(f'  generate {target}')
                try:
                    if topics is None:
                        model = model if not isinstance(model, LazyPyTopicModelLoader) else model()
                        topics = [
                            [word for word, _ in model.get_words_of_topic_sorted(x) if keep_phrases or ' ' not in word] for
                            x in range(model.k)]
                    if isinstance(data, LazyCoherenceModelData):
                        data = data()
                    coherence = CoherenceModelKwArgs(
                        topics=topics,
                        texts=data.corpus_texts,
                        dictionary=data.dictionary,
                        corpus=data.gensim_corpus,
                        topn=topn,
                        coherence=target,
                        window_size=window_size,
                    )
                    q = multiprocessing.Queue()
                    failed = False
                    p = multiprocessing.Process(target=_execute_get_coherence, args=(q, coherence))
                    p.start()
                    p.join(60 * timeout_for_calculation)
                    if p.exitcode != 0:
                        failed = True
                    p.close()
                    del p
                    if failed:
                        q.close()
                        print(f'  failed {target}')
                        continue

                    value = q.get_nowait()
                    q.close()
                    del q

                    if not isinstance(value, float):
                        print(f"Failed with:")
                        print(value)
                        del value
                        continue

                except Exception as e:
                    print(f"Bad Error with:")
                    print(e)
                    continue
                coherence_dir.save_coherence(
                    target,
                    value
                )
                result[target] = value
    return result



def calculate_coocurrences(
        lang_a: str,
        lang_b: str,
        input_path: Path | PathLike | str,
        data_dir: DataDirectory,
        marker: str,
        token_filter: TokenCountFilter | None = None,
        topn: int = 20,
        window_size: int | None = None,
        coocurrences: typing.Iterable[str] | None = None,
        keep_phrases: bool = False,
        timeout_for_calculation: int | None = None,
):
    """
    timeout_for_calculation: in minutes
    """
    print("Load Corpora")
    data_a = LazyCoherenceModelData(lang_a, input_path, data_dir, token_filter=token_filter)
    data_b = LazyCoherenceModelData(lang_a, input_path, data_dir, token_filter=token_filter, corpus_language=lang_b)
    print("Cleaned up corpora\nStart creating coherences.")
    coocurrences = coocurrences if coocurrences is not None else ('u_mass', 'c_v', 'c_uci', 'c_npmi', 'c_w2v')
    assert coocurrences is not None

    original = {
        k: v if isinstance(v, float) else v.get_coherence() for k, v in calculate_and_store_coocurrence_single(
            LazyPyTopicModelLoader(data_dir.load_original_py_model),
            data_dir.coherences,
            data_a,
            coocurrences,
            topn=topn,
            window_size=window_size,
            keep_phrases=keep_phrases,
            timeout_for_calculation=timeout_for_calculation
        ).items()
    }

    other = [
        (translation.name, {k: v if isinstance(v, float) else v.get_coherence() for k, v in calculate_and_store_coocurrence_single(
            LazyPyTopicModelLoader(lambda: translation.model_uncached),
            translation.coherences,
            data_b,
            coocurrences,
            topn=topn,
            window_size=window_size,
            keep_phrases=keep_phrases,
            timeout_for_calculation=timeout_for_calculation
        ).items()}) for translation in data_dir.iter_all_translations()
    ]

    s = [
        ("model", ) + tuple(coocurrences),
        ("original",) + tuple(original[value] for value in coocurrences)
    ]

    for name, value in other:
        to_append = [name]
        to_append.extend(value[targ] for targ in coocurrences)
        s.append(tuple(to_append))
    targ = data_dir.root_dir / f'coocurrences_{marker}.txt'
    targ.parent.mkdir(parents=True, exist_ok=True)
    with targ.open('w', encoding="utf-8", buffering=256*1024*1024) as f:
        for value in s:
            for i, cont in enumerate(value):
                if i > 0:
                    f.write(' & ')
                if isinstance(cont, str):
                    if '_' in cont:
                        splitted = cont.split('_')
                        cont = splitted[0] + '_' + '_'.join([f'{{{value}}}' for value in splitted[1:]])
                    f.write(cont)
                elif isinstance(cont, float):
                    f.write(f'{cont:.5f}')
            f.write('\\\\\n')
