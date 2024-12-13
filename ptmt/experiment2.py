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
from pathlib import Path

import numpy
from ldatranslate import PyTopicModel, PyDictionary, PyTranslationConfig, PyBasicBoostConfig, NormalizeMode
from ldatranslate import FDivergence, Domain, Register, ScoreModifierCalculator, PyHorizontalBoostConfig

from ptmt.research.dirs import DataDirectory, sizeof_fmt
from ptmt.research.protocols import TranslationConfig
from ptmt.research.tmt1.run import run

def modifier_factory(
        divergence: FDivergence,
        alpha: None | float = None,
        score_mod: ScoreModifierCalculator | None = None,
) -> typing.Callable[[TranslationConfig, PyTopicModel, PyDictionary], PyTranslationConfig]:
    def config_modifier(config: TranslationConfig, _: PyTopicModel, dictionary: PyDictionary) -> PyTranslationConfig:

        counts: dict[Domain | Register | int, int] = dictionary.dictionary_meta_counts().a().as_dict()

        target_value = numpy.percentile(
            list(counts.values()),
            10
        )

        targets = []
        for k, v in counts.items():
            if v >= target_value:
                targets.append(k)

        return PyTranslationConfig(
            None,
            None,
            config.keep,
            None,
            None,
            PyHorizontalBoostConfig(
                PyBasicBoostConfig(
                    divergence,
                    alpha,
                    targets,
                    False,
                    score_mod or ScoreModifierCalculator.WeightedSum
                ),
                NormalizeMode.Sum,
                0.15,
                False
            )
        )
    return config_modifier

if __name__ == '__main__':
    """The experiments for the paper 'TMT: A Simple Way to Translate Topic Models Using Dictionaries'."""
    run(
        experiment_name="kl_weighted_sum",
        target_folder="../data/experiment3",
        path_to_original_dictionary="../data/final_dict/dictionary_20241130_proc3.dat.zst",
        path_to_raw_data="../data/aligned_articles_corpus/wikicomp-2014_deen.xml.bz2",
        temp_folder=r'E:\tmp\TempGen',
        config_modifier=modifier_factory(FDivergence.KL),
        clean_translations=True
    )

    run(
        experiment_name="bhattacharyya_weighted_sum",
        target_folder="../data/experiment3",
        path_to_original_dictionary="../data/final_dict/dictionary_20241130_proc3.dat.zst",
        path_to_raw_data="../data/aligned_articles_corpus/wikicomp-2014_deen.xml.bz2",
        temp_folder=r'E:\tmp\TempGen',
        config_modifier=modifier_factory(FDivergence.Bhattacharyya),
        clean_translations=True
    )

    run(
        experiment_name="kl_weighted_sum",
        target_folder="../data/experiment4",
        path_to_original_dictionary="../data/final_dict/dictionary_20241130_proc4.dat.zst",
        path_to_raw_data="../data/aligned_articles_corpus/wikicomp-2014_deen.xml.bz2",
        temp_folder=r'E:\tmp\TempGen',
        config_modifier=modifier_factory(FDivergence.KL),
        clean_translations=True
    )

    run(
        experiment_name="bhattacharyya_weighted_sum",
        target_folder="../data/experiment4",
        path_to_original_dictionary="../data/final_dict/dictionary_20241130_proc4.dat.zst",
        path_to_raw_data="../data/aligned_articles_corpus/wikicomp-2014_deen.xml.bz2",
        temp_folder=r'E:\tmp\TempGen',
        config_modifier=modifier_factory(FDivergence.Bhattacharyya),
        clean_translations=True
    )