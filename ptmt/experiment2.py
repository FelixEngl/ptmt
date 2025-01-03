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
import dataclasses
import typing
from os import PathLike
from pathlib import Path
from typing import Optional

import numpy
from ldatranslate import PyTopicModel, PyDictionary, PyTranslationConfig, PyNGramStatistics
from ldatranslate import (FDivergence, Domain, Register, ScoreModifierCalculator, MeanMethod,
                          BoostNorm)

from ptmt.create.basic import create_basic_boost_factory
from ptmt.create.horizontal import HorizontalBoostFactory, HorizontalKwargs, create_horizontal_factory
from ptmt.create.ngram import NGramBoostKwargs, NGramFactory, create_ngram_language_boost_factory
from ptmt.create.vertical import VerticalBoostFactory, VerticalKwargs, create_vertical_factory
from ptmt.research.protocols import TranslationConfig
from ptmt.research.tmt1.run import run

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


class RunKwargs(typing.TypedDict):
    experiment_name: str
    target_folder: Path | PathLike | str
    path_to_original_dictionary: Path | PathLike | str
    path_to_raw_data: typing.NotRequired[Path | PathLike | str]
    temp_folder: typing.NotRequired[Path | PathLike | str]
    config_modifier: typing.NotRequired[typing.Callable[[TranslationConfig, PyTopicModel, PyDictionary], PyTranslationConfig]]
    clean_translations: typing.NotRequired[bool]
    skip_if_finished_marker_set: typing.NotRequired[bool]
    global_model_dir: typing.NotRequired[Path | PathLike | str]
    ngrams: typing.NotRequired[Path | PathLike | str | None | PyNGramStatistics]


def create_run(
        name: str,
        identifier: str,
        dictionary_file_name: str,
        *,
        vertical: Optional[VerticalKwargs] = None,
        horizontal: Optional[HorizontalKwargs] = None,
        ngram: Optional[NGramBoostKwargs] = None,
        clean_translations: bool = False,
) -> tuple[dict[str, typing.Any], RunKwargs]:
    if vertical is not None:
        name += "_v_"
        name += str(hash(tuple(sorted(vertical.items(), key=lambda item: item[0]))))

        vertical = create_vertical_factory(
            create_basic_boost_factory(
                **vertical,
            ),
            **vertical
        )
    if horizontal is not None:
        name += "_h_"
        name += str(hash(tuple(sorted(horizontal.items(), key=lambda item: item[0]))))
        horizontal = create_horizontal_factory(
            create_basic_boost_factory(
                **horizontal,
            ),
            **horizontal
        )

    if ngram is not None:
        name += "_n_"
        name += str(hash(tuple([(value[0], tuple([x for x in value[1].items()])) for value in sorted(ngram.items(), key=lambda item: item[0])])))


        name += str(hash(tuple()))
        ngram = create_ngram_language_boost_factory(
            **ngram,
        )

    targ = {
        "name": name,
        "vertical": vertical,
        "horizontal": horizontal,
        "ngram": ngram,
    }

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
        global_model_dir=f"../data/{identifier}/shared"
    )

if __name__ == '__main__':
    """The experiments for the paper 'TMT: A Simple Way to Translate Topic Models Using Dictionaries'."""
    configs = [
        create_run(
            "v3",
            "experiment4",
            "dictionary_20241130_proc4",
            horizontal={
                "divergence": FDivergence.KLReversed,
                "factor": 8,
                "score_mod": ScoreModifierCalculator.WeightedSum,
                "mean": MeanMethod.GeometricMean,
                "linear_transformed": False,
                "h_alpha": 0.1,
            },
            vertical={
                "divergence": FDivergence.Hellinger,
                "score_mod": ScoreModifierCalculator.WeightedSum,
                "norm": BoostNorm.Off,
                "factor": 6,
            },
            clean_translations=True
        ),
    ]

    for i, info_and_cfg in enumerate(configs):
        info, cfg = info_and_cfg
        print(f"Run {i+1}/{len(configs)}")
        print(f"{cfg}")

        run(**cfg)
