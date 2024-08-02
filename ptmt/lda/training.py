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

import sys
from os import PathLike
from pathlib import Path
import tomotopy as tp
from ptmt.lda.topic_model import SimpleTopicModel


def export_tomotopy(model: tp.LDAModel, path: Path | str):
    lda = SimpleTopicModel(model=model)
    lda.save(path)
    lda.visualize(path / 'visualisation.html')
    with (path/'summary.txt').open('w', encoding='UTF-8', newline='\n') as w:
        lda.summary(file=w)


def create_by_corpus(corpus: tp.utils.Corpus, **kwargs) -> tp.LDAModel:
    kwargs.setdefault('tw', tp.TermWeight.ONE)
    kwargs.setdefault('min_cf', 3)
    kwargs.setdefault('rm_top', 5,)
    kwargs.setdefault('k', 25)
    kwargs.setdefault('seed', 1234)
    mdl = tp.LDAModel(**kwargs)
    mdl.add_corpus(corpus)
    return mdl

def run_lda(mdl: tp.LDAModel, output_path: Path | str | PathLike[str], iters: None | int = None) -> Path:
    if not isinstance(output_path, Path):
        output_path = Path(output_path)
    mdl.burn_in = 100
    mdl.train(0)
    print('Num docs:', len(mdl.docs), ', Vocab size:', len(mdl.used_vocabs), ', Num words:', mdl.num_words)
    print('Removed top words:', mdl.removed_top_words)
    print('Training...', file=sys.stderr, flush=True)
    for i in range(0, iters if iters else 1000, 10):
        mdl.train(10)
        print('Iteration: {}\tLog-likelihood: {}'.format(i, mdl.ll_per_word))

    mdl.summary()
    print('Saving...', file=sys.stderr, flush=True)

    save_path = output_path / 'trained_lda'
    save_path.mkdir(parents=True, exist_ok=True)

    mdl.save(str(output_path / 'lda_model.tomotopy.bin'), True)

    for k in range(mdl.k):
        print('Topic #{}'.format(k))
        for word, prob in mdl.get_topic_words(k):
            print('\t', word, prob, sep='\t')

    export_tomotopy(mdl, save_path)
    return output_path

