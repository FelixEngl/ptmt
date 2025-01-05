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
import pprint
from typing import Callable

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
        configs: typing.Iterable[TranslationConfig] | Callable[[], typing.Iterable[TranslationConfig]] | None = None,
        shared_dir: Path | PathLike | str | None = None,
) -> tuple[dict[str, Any], RunKwargs]:
    a, b, c = create_name(vertical, horizontal, ngram)
    name = f'{name}_{a}_{b}_{c}'
    targ = {
        "name": name,
        "vertical": vertical,
        "horizontal": horizontal,
        "ngram": ngram,
    }


    if vertical is not None and len(vertical) > 0:
        vertical = create_vertical_factory(
            create_basic_boost_factory(
                **vertical,
            ),
            **vertical
        )
    else:
        vertical = None

    if horizontal is not None and len(horizontal) > 0:
        horizontal = create_horizontal_factory(
            create_basic_boost_factory(
                **horizontal,
            ),
            **horizontal
        )
    else:
        horizontal = None

    if ngram is not None and len(ngram) > 0:
        ngram = create_ngram_language_boost_factory(**ngram)
    else:
        ngram = None

    shared_dir = shared_dir if shared_dir is not None else Path(f"../data/{identifier}/shared")

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
        shared_dir=shared_dir,
        ngram_statistics=ngram_statistics,
        configs=configs
    )



def short_configs() -> list[TranslationConfig]:
    return list(filter(lambda v: v.config_id[0] in ('P', 'U', 'O', 'L', 'T', 'J', 'A', 'B', 'C'), create_configs()))

if __name__ == '__main__':
    """The experiments for the paper 'TMT: A Simple Way to Translate Topic Models Using Dictionaries'."""

    print(
        list(create_all_configs())
    )

    gen = set()
    for i, hvn in enumerate(itertools.chain(
        [(None, None, None)],
        create_all_configs()
    )):
        horizontal, vertical, ngram = hvn
        info, cfg = create_run(
            "v3",
            "experiment4",
            "dictionary_20241130_proc3",
            "../data/ngrams/counts_with_proc.bin",
            horizontal=horizontal,
            vertical=vertical,
            ngram=ngram,
            clean_translations=True,
            configs=short_configs,
            shared_dir=f"../data/experiment3/shared"
        )
        old = len(gen)
        gen.add(info['name'])
        if old == len(gen):
            continue
        print(f"Run {i + 1}: {info['name']}")
        pprint.pprint(f"{cfg}")
        run(**cfg)