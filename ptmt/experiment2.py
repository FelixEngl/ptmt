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

from ptmt.experiment2_support.functions import *
from ptmt.research.protocols import TranslationConfig
from ptmt.research.tmt1.configs import create_configs
from ptmt.research.tmt1.run import run, RunKwargs


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
) -> tuple[dict[str, Any], RunKwargs]:
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



def short_configs() -> list[TranslationConfig]:
    return list(filter(lambda v: v.config_id[0] in ('P', 'U', 'O'), create_configs()))

if __name__ == '__main__':
    """The experiments for the paper 'TMT: A Simple Way to Translate Topic Models Using Dictionaries'."""
    # print(determine_all_combinations())
    # short_configs()
    # exit(0)

    configs = [
        create_run(
            "v3",
            "experiment3",
            "dictionary_20241130_proc3",
            "../data/ngrams/counts_with_proc.bin",
            horizontal=None,
            vertical=None,
            ngram=None,
            clean_translations=True
        ),
    ]

    for i, info_and_cfg in enumerate(configs):
        info, cfg = info_and_cfg
        print(f"Run {i+1}/{len(configs)}")
        print(f"{cfg}")
        run(**cfg)
