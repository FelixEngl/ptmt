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
import typing
from enum import Enum
from os import PathLike
from pathlib import Path
from typing import Optional

import numpy
from ldatranslate import PyTopicModel, PyDictionary, PyTranslationConfig, PyNGramStatistics, Idf, NormalizeMode
from ldatranslate import (FDivergence, Domain, Register, ScoreModifierCalculator, MeanMethod,
                          BoostNorm)
from ldatranslate.ldatranslate import BoostMethod

from ptmt.create.basic import create_basic_boost_factory
from ptmt.create.horizontal import HorizontalBoostFactory, HorizontalKwargs, create_horizontal_factory
from ptmt.create.ngram import NGramBoostKwargs, NGramFactory, create_ngram_language_boost_factory
from ptmt.create.vertical import VerticalBoostFactory, VerticalKwargs, create_vertical_factory
from ptmt.research.protocols import TranslationConfig
from ptmt.research.tmt1.run import run, RunKwargs


def modifier_factory(
    *,
    vertical: Optional[VerticalBoostFactory] = None,
    horizontal: Optional[HorizontalBoostFactory] = None,
    ngram: Optional[NGramFactory] = None,
) -> typing.Callable[[TranslationConfig, PyTopicModel, PyDictionary], PyTranslationConfig]:
    def config_modifier(config: TranslationConfig, _: PyTopicModel, dictionary: PyDictionary) -> PyTranslationConfig:

        counts: dict[Domain | Register | int, int] = dictionary.dictionary_meta_counts().a().as_dict()

        target_value = numpy.percentile(
            list(counts.values()),
            10
        )

        targets: list[Domain | Register | int] = []
        for k, v in counts.items():
            if v >= target_value:
                targets.append(k)

        a = None
        if vertical is not None:
            a = vertical(targets)
        b = None
        if horizontal is not None:
            b = horizontal(targets)

        c = None
        if ngram is not None:
            c = ngram()

        return PyTranslationConfig(
            None,
            None,
            config.keep,
            None,
            a,
            b,
            c
        )
    return config_modifier


def _single_word(k: str, v: typing.Any) -> str:
    if isinstance(v, float):
        u = f'{v:.4f}'.replace('.', '-')
    # elif isinstance(v, FDivergence):
    #     u = str(v)
    #     u = u[0:min(len(u), 3)]
    elif (isinstance(v, MeanMethod)
          or isinstance(v, BoostMethod)
          or isinstance(v, ScoreModifierCalculator)
          or isinstance(v, BoostNorm)
          or isinstance(v, FDivergence)
          or isinstance(v, NormalizeMode)
    ):
        u = ''.join(filter(lambda c: c.isupper(), str(v)))
    elif isinstance(v, dict):
        return _compact(f"bo{k[-1]}", v)
    else:
        u = str(v)[0]
    return f'{k[0]}{u}'

def _compact(start: str, info: dict[str, typing.Any] | None) -> str:
    s1 = start
    if info is not None:
        for k, v in info.items():
            s1 += _single_word(k, v)
    else:
        s1 += '#'
    return s1

def create_name(
        vertical: Optional[VerticalKwargs] = None,
        horizontal: Optional[HorizontalKwargs] = None,
        ngram: Optional[NGramBoostKwargs] = None,
) -> tuple[str, str, str]:
    v = _compact('V', vertical)
    h = _compact('H', horizontal)
    n = _compact('N', ngram)
    return v, h, n





def create_run(
        name: str,
        identifier: str,
        dictionary_file_name: str,
        ngram_statistics: Path | PathLike | str | None | PyNGramStatistics = None,
        *,
        vertical: Optional[VerticalKwargs] = None,
        horizontal: Optional[HorizontalKwargs] = None,
        ngram: Optional[NGramBoostKwargs] = None,
        clean_translations: bool = False,
) -> tuple[dict[str, typing.Any], RunKwargs]:
    a, b, c = create_name(vertical, horizontal, ngram)
    name = f'{name}_{a}_{b}_{c}'
    targ = {
        "name": name,
        "vertical": vertical,
        "horizontal": horizontal,
        "ngram": ngram,
    }


    if vertical is not None:
        vertical = create_vertical_factory(
            create_basic_boost_factory(
                **vertical,
            ),
            **vertical
        )
    if horizontal is not None:
        horizontal = create_horizontal_factory(
            create_basic_boost_factory(
                **horizontal,
            ),
            **horizontal
        )

    if ngram is not None:
        ngram = create_ngram_language_boost_factory(
            **ngram,
        )

    return targ, RunKwargs(
        experiment_name=name,
        target_folder=f"../data/{identifier}",
        path_to_original_dictionary=f"../data/final_dict/{dictionary_file_name}.dat.zst",
        path_to_raw_data="../data/aligned_articles_corpus/wikicomp-2014_deen.xml.bz2",
        temp_folder=r'E:\tmp\TempGen',
        config_modifier= modifier_factory(
            vertical=vertical,
            horizontal=horizontal,
            ngram=ngram
        ),
        clean_translations=clean_translations,
        skip_if_finished_marker_set=False,
        global_model_dir=f"../data/{identifier}/shared",
        ngram_statistics=ngram_statistics
    )


def iter_test(t: type):
    for x in filter(lambda x: '_' not in x, dir(t)):
        yield getattr(t, x)

if __name__ == '__main__':
    """The experiments for the paper 'TMT: A Simple Way to Translate Topic Models Using Dictionaries'."""

    configs = [
        create_run(
            "v3",
            "experiment3",
            "dictionary_20241130_proc3",
            "../data/ngrams/counts_with_proc.bin",
            horizontal={
                "divergence": FDivergence.KL,
                "score_mod": ScoreModifierCalculator.WeightedSum,
                "normalize_mode": NormalizeMode.Sum,
                "linear_transformed": False,
                "h_alpha": 0.1,
                'booster': BoostMethod.Linear,
                'mean': MeanMethod.GeometricMean
            },
            vertical={
                "divergence": FDivergence.Bhattacharyya,
                "score_mod": ScoreModifierCalculator.Max,
                "norm": BoostNorm.Linear,
            },
            ngram={
                'boost_lang_a': {
                    'idf': Idf.InverseDocumentFrequency,
                    'boosting': BoostMethod.Linear,
                    'norm': BoostNorm.Off,
                    'only_positive_boost': True
                },
                'boost_lang_b': {
                    'idf': Idf.InverseDocumentFrequency,
                    'boosting': BoostMethod.Linear,
                    'norm': BoostNorm.Linear,
                    'only_positive_boost': True,
                    'factor': 0.5
                }
            },
            clean_translations=True
        ),
    ]

    for i, info_and_cfg in enumerate(configs):
        info, cfg = info_and_cfg
        print(f"Run {i+1}/{len(configs)}")
        print(f"{cfg}")
        run(**cfg)
