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
from os import PathLike
from pathlib import Path
from typing import Callable

from ldatranslate import PyStemmingAlgorithm, TokenCountFilter, PyTopicModel, PyDictionary, PyTranslationConfig
from ldatranslate.ldatranslate import PyNGramStatistics
from matplotlib.pyplot import colormaps

from ptmt.research.helpers.article_processor_creator import PyAlignedArticleProcessorKwArgs
from ptmt.research.plotting.generate_plots import MPLColor
from ptmt.research.protocols import TranslationConfig
from ptmt.research.tmt1.pipeline import run_pipeline, LinePlotKWArgs, BarPlotKWArgs, CoocurrencesKwArgs
from ptmt.research.tmt1.toolkit.test_ids import test_ids
from ptmt.toolkit.stopwords import get_stop_words

en_stopwords = get_stop_words("english")
en_stopwords.add("to")
en_stopwords.add("sb")
en_stopwords.add("the")
en_stopwords.add("sth")
en_stopwords.add("so")

de_stopwords = get_stop_words("german")
de_stopwords.add("ein")
de_stopwords.add("eine")
de_stopwords.add("einer")
de_stopwords.add("eines")
de_stopwords.add("einem")
de_stopwords.add("etwas")
de_stopwords.add("etw")
de_stopwords.add("jdm")
de_stopwords.add("jmdm")


default_processor_kwargs = PyAlignedArticleProcessorKwArgs(
    stopwords_a=en_stopwords,
    stopwords_b=de_stopwords,
    stemmer_a=PyStemmingAlgorithm.English,
    stemmer_b=PyStemmingAlgorithm.German,
)


def color_provider3(text: str) -> MPLColor | None:
    match (text[0], text[1]):
        case ('A' | 'B' | 'C', _) | ('D', 'L'):
            return '#000000'
        case ('P' | 'Q' | 'R', _):
            return '#E50000'
        case ('S' | 'T' | 'U', _):
            return '#C20078'
        case ('M' | 'N' | 'O', _):
            return '#F97306'
        case ('D' | 'E' | 'F', _):
            return '#15B01A'
        case ('G' | 'H' | 'I', _):
            return '#029386'
        case ('V' | 'W' | 'X', _):
            return '#0343DF'
        case ('J' | 'K' | 'L', _):
            return '#000080'
        case _:
            print(f"Unknown {text}!")
    return None


def run(
        experiment_name: str,
        target_folder: Path | PathLike | str,
        path_to_original_dictionary: Path | PathLike | str,
        path_to_raw_data: Path | PathLike | str | None = None,
        temp_folder: Path | PathLike | str | None = None,
        deepl: bool = False,
        configs: typing.Iterable[TranslationConfig] | Callable[[], typing.Iterable[TranslationConfig]] | None = None,
        config_modifier: Callable[[TranslationConfig, PyTopicModel, PyDictionary], PyTranslationConfig] | None = None,
        highlight: tuple[str,...] | None = None,
        clean_translations: bool = False,
        skip_if_finished_marker_set: bool = True,
        global_model_dir: Path | PathLike | str | None = None,
        ngrams: Path | PathLike | str | None | PyNGramStatistics = None,
):
    target_folder = target_folder if isinstance(target_folder, Path) else Path(target_folder)

    path_to_extracted_data = target_folder / "preprocessed" / "extracted_data.bulkjson"

    if not path_to_extracted_data.exists():
        print(f"{path_to_extracted_data} does not exist! Trying to create the preprocessed data.")
        assert path_to_raw_data is not None, \
            f"The extracted data was not found at {path_to_extracted_data}, requires a path_to_raw_data!"
        path_to_raw_data = path_to_raw_data \
            if isinstance(path_to_raw_data, Path) \
            else Path(path_to_raw_data)

        assert path_to_raw_data.exists(), \
            f"The extracted data was not found at {path_to_extracted_data} but the path to the raw data {path_to_raw_data} is also not existing!"

        # No need to import if not necessary.
        from ptmt.corpus_extraction import extract_wikicomp_into

        path_to_extracted_data.parent.mkdir(parents=True, exist_ok=True)

        extract_wikicomp_into(
            path_to_raw_data,
            path_to_extracted_data,
            path_to_extracted_data.parent / f"extracted_data_categories.json"
        )

        print("Finished preprocessing data.")

    # if highlight is None:
    #     highlight = ("P5", "G5", "P3", "M3", "C5*", "B3*")

    run_pipeline(
        experiment_name,
        "en",
        "de",
        path_to_extracted_data,
        target_folder, # root_dir
        path_to_original_dictionary,
        "my_dictionary.dat.zst",
        "f",
        test_ids,
        default_processor_kwargs,
        TokenCountFilter(50, 1000),
        temp_folder,
        1000,
        deepl,
        mark_baselines=True,
        generate_Excel=False,
        ndcg_kwargs={
            "top_n_weigts": (3, 2, 1)
        },
        line_plot_args=LinePlotKWArgs(
            colors=colormaps.get("prism")
        ),
        bar_plot_args=BarPlotKWArgs(
            highlight= highlight,
            label_rotation=270,
            y_label_rotation=270,
            y_label_labelpad=20,
            label_colors=color_provider3
        ),
        coocurences_kwargs=False,
        configs = configs,
        config_modifier=config_modifier,
        clean_translations=clean_translations,
        skip_if_finished_marker_set=skip_if_finished_marker_set,
        global_model_dir=global_model_dir,
        ngram=ngrams
    )



