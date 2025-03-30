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
import encodings
import json
import math
import os
import shutil
from os import PathLike
from typing import TypedDict

import matplotlib
from fraction import Fraction
from ldatranslate import *
from matplotlib import pyplot as plt

from ptmt.dictionary_readers.v1.dictionaries import DictionaryReaderLike
from ptmt.dictionary_readers.v1.dictionary_reader_declarations import *
from ptmt.research.dirs import sizeof_fmt
from ptmt.research.helpers.article_processor_creator import create_processor, PyAlignedArticleProcessorKwArgs
from ptmt.research.helpers.chunking import chunk_by
from ptmt.research.helpers.fonts import FontSizes
from ptmt.research.lda_model import DataDirectory
from ptmt.research.plotting.generate_plots import PlotData, render_bar_plot, render_x_bars, TitlesAndLabels, MPLColor
from ptmt.research.plotting.highlight_resolver import resolve_highlight, resolve_highlight_to_idx
from ptmt.research.protocols import TranslationConfig
from ptmt.research.tmt1.configs import create_configs
from ptmt.research.tmt1.toolkit.coherences import calculate_coocurrences
from ptmt.research.tmt1.toolkit.data_creator import create_train_data
from ptmt.research.tmt1.toolkit.deepl import deepl_translate
from ptmt.research.tmt1.toolkit.dictionary_creation import make_dictionary
from ptmt.research.tmt1.toolkit.model_training import train_models
from ptmt.research.tmt1.toolkit.model_translation import SINGLE_FILTER, translate_models, DefectModelError
from ptmt.research.tmt1.toolkit.tables import output_table
from ptmt.research.tmt1.toolkit.unstemm_dict_creation import create_unstemm_dictionary


class NDCGKwArgs(TypedDict, total=False):
    top_n_weigts: tuple[int, ...]
    save: bool
    ignore_existing_file: bool


class CoocurrencesKwArgs(TypedDict, total=False):
    topn: int
    window_size: int | None
    coocurrences: typing.Iterable[str] | None
    keep_phrases: bool
    timeout_for_calculation: int | None
    """
    timeout_for_calculation: in minutes
    """


class BarPlotKWArgs(TypedDict, total=False):
    id_rows: int
    id_row_boost: float
    id_row_delta: float
    label_rotation: str | float | None
    show_buildup: bool
    number_of_ndcg_value_ticks: int
    font_sizes: FontSizes
    titles_and_labels: TitlesAndLabels | None
    linewidth: float
    width: float
    edgecolor: str
    highlight:  typing.Iterable[str | int]
    y_label_rotation: str | float | None
    y_label_labelpad: float
    vertical_alignment: typing.Literal["bottom", "baseline", "center", "center_baseline", "top"]
    horizontal_alignment: typing.Literal["left", "center", "right"]
    delta_x: float | None
    label_colors: dict[str, MPLColor] | Callable[[str], MPLColor | None] | None


class LinePlotKWArgs(TypedDict, total=False):
    targets: typing.Iterable[str | int]
    colors: matplotlib.colors.ListedColormap | matplotlib.colors.LinearSegmentedColormap | None
    fig_args: dict[str, typing.Any]



class _RunSingleKWArgs(TypedDict):
    original_data_path: Path
    processor: PyAlignedArticleProcessor
    # data_dir: DataDirectory
    inp: Path
    test_ids: list[int] | Fraction
    token_filter: TokenCountFilter | None
    iters: int | None
    lang_a: str
    lang_b: str
    dictionary: PyDictionary
    limit: int | None
    stop_words: dict[str, PyStopWords] | None
    filters: tuple[SINGLE_FILTER, SINGLE_FILTER] | None
    deepl: bool
    translate_mode: typing.Literal["simple", "complex"]
    mark_baselines: bool
    generate_Excel: bool | int | tuple[int, ...]
    coocurences_kwargs: CoocurrencesKwArgs | bool
    ndcg_kwargs: NDCGKwArgs | None
    bar_plot_args: BarPlotKWArgs | None
    line_plot_args: LinePlotKWArgs | None
    configs: typing.Iterable[TranslationConfig] | Callable[[], typing.Iterable[TranslationConfig]]
    config_modifier: Callable[[TranslationConfig, PyTopicModel, PyDictionary], PyTranslationConfig] | None
    clean_translation: bool
    skip_if_finished_marker_set: bool
    ngram_statistics: PyNGramStatistics | None
    min_not_nan: int | float | None



def _print_big_view(data_dir: DataDirectory):
    with data_dir.simple_text_view_path.open(mode="w", encoding='utf-8') as o:
        for value in data_dir.iter_all_translations():
            topic_model = value.model_uncached
            o.write(f"--------- {value.name} ---------\n")
            for topic_nr in range(topic_model.k):
                o.write(f"  Topic ID: {topic_nr}\n\n")
                for entry in topic_model.get_words_of_topic_sorted(topic_nr)[:30]:

                    o.write(f"    {entry[0]}: {entry[1]:0.5f}\n")
                o.write("\n~~~~~~~~~~~\n")


def run_single(
        marker: str,
        data_dir: DataDirectory,
        original_data_path: Path,
        processor: PyAlignedArticleProcessor,
        inp: Path,
        test_ids: list[int] | Fraction,
        token_filter: TokenCountFilter | None,
        iters: int | None,
        lang_a: str,
        lang_b: str,
        dictionary: PyDictionary,
        limit: int | None,
        stop_words: dict[str, PyStopWords] | None,
        filters: tuple[SINGLE_FILTER, SINGLE_FILTER] | None,
        deepl: bool,
        translate_mode: typing.Literal["simple", "complex"],
        mark_baselines: bool,
        generate_Excel: bool | int | tuple[int, ...],
        coocurences_kwargs: CoocurrencesKwArgs | bool,
        ndcg_kwargs: NDCGKwArgs | None,
        bar_plot_args: BarPlotKWArgs | None,
        line_plot_args: LinePlotKWArgs | None,
        configs: typing.Collection[TranslationConfig] | Callable[[], typing.Collection[TranslationConfig]],
        config_modifier: Callable[[TranslationConfig, PyTopicModel, PyDictionary], PyTranslationConfig] | None,
        clean_translation: bool,
        skip_if_finished_marker_set: bool,
        ngram_statistics: PyNGramStatistics | None,
        min_not_nan: int | float | None
) -> DataDirectory:
    if skip_if_finished_marker_set and data_dir.is_finished():
        print(f"{data_dir.root_dir} is already finished.")
        return data_dir
    else:
        data_dir.rm_is_finished()
    
    print(f"Create for {marker}")
    lang_a = str(LanguageHint(lang_a))
    lang_b = str(LanguageHint(lang_b))

    if stop_words is None:
        stop_words = {
            lang_a: processor[lang_a].create_stopword_filter(),
            lang_b: processor[lang_b].create_stopword_filter()
        }

    train, test = create_train_data(
        inp,
        data_dir.shareable_paths,
        test_ids,
        token_filter,
        (processor, original_data_path),
        stop_words
    )
    print(f"train: {train}, test: {test}")
    train_models(
        lang_a,
        train,
        data_dir,
        token_filter,
        iters
    )

    if deepl:
        print("Execute deepl")
        o_dict = create_unstemm_dictionary(lang_a, train, data_dir)
        print("Created deepl dict!")
        deepl_translate(o_dict, data_dir, translate_mode, processor, lang_b, test, limit)

    print("Finished training model\nStart translating")
    try:
        translate_models(
            lang_a,
            lang_b,
            data_dir,
            dictionary,
            ngram_statistics,
            test,
            limit,
            filters,
            configs=configs,
            config_modifier=config_modifier,
            min_not_nan=min_not_nan
        )
    except DefectModelError as e:
        print("The confiuration failed to translate the topic model properly!")
        data_dir.mark_as_finished()
        raise e
    print("Finished translating models")



    print("Start ndcg")

    if ndcg_kwargs is None:
        ndcg_kwargs: NDCGKwArgs = NDCGKwArgs()
    ndcg_kwargs.setdefault("top_n_weigts", (1, 1, 1))
    ndcg_kwargs.setdefault("save", False)
    ndcg_kwargs.setdefault("ignore_existing_file", True)
    print(f"Execute NDCG with {ndcg_kwargs}")

    output_table(data_dir, marker)



    _print_big_view(data_dir)


    if not isinstance(coocurences_kwargs, bool) or coocurences_kwargs:
        if isinstance(coocurences_kwargs, bool):
            coocurences_kwargs = CoocurrencesKwArgs(
                topn=20,
                window_size=None,
                coocurrences=None,
                keep_phrases=False,
                timeout_for_calculation=None
            )
        calculate_coocurrences(
            lang_a,
            lang_b,
            train,
            data_dir,
            marker,
            token_filter,
            **coocurences_kwargs
        )


    for value in data_dir.iter_all_translations():
        if value.ndcg_path.exists() and ndcg_kwargs is None:
            continue
        if ndcg_kwargs is not None:
            value.calculate_ndcg_for(**ndcg_kwargs)
        else:
            value.calculate_ndcg_for((1, 1, 1), save=True)
    print("Calculated NDCG@3!")

    to_plot = PlotData(data_dir, 3, mark_baselines=mark_baselines)
    print("Generated Plot data")



    best_baseline = math.inf
    worst_non_baseline = -math.inf
    deep_baseline = 0
    for i, value in enumerate(to_plot.ranking_sorted):
        if value.is_baseline and value.name_no_star != data_dir.deepl().name:
            if best_baseline > i:
                best_baseline = i
        elif value.name_no_star == data_dir.deepl().name:
            deep_baseline = i
        else:
            if worst_non_baseline < i:
                worst_non_baseline = i
    assert not math.isinf(best_baseline), "No best_baseline found!"
    assert not math.isinf(worst_non_baseline), "No worst_non_baseline found!"

    targets: tuple[float|int, ...] = tuple(sorted({
        0,
        int((len(to_plot.ranking) - 1) / 2),
        int((len(to_plot.ranking) - 1) / 2) + 1,
        best_baseline,
        worst_non_baseline,
        deep_baseline,
        len(to_plot.ranking) - 1
    }))


    if bar_plot_args is None:
        bar_plot_args = BarPlotKWArgs()
    if bar_plot_args.get('highlight', None) is None:
        bar_plot_args['highlight'] = targets
    bar_plot_args.setdefault('highlight', targets)
    bar_plot_args.setdefault('width', 1.0)
    bar_plot_args.setdefault('edgecolor', 'black')
    bar_plot_args.setdefault('linewidth', 0.05)
    bar_plot_args.setdefault('number_of_ndcg_value_ticks', 7)
    bar_plot_args.setdefault('font_sizes', FontSizes().set_size(18, 'label', 'a').set_size(14, 'ticks', 'a').set_size(16, 'legend', 'a'))
    bar_plot_args.setdefault('show_buildup', False)
    bar_plot_args.setdefault('titles_and_labels', None)
    bar_plot_args.setdefault('id_row_boost', 0.1)
    bar_plot_args.setdefault('id_row_delta', -0.1)
    bar_plot_args.setdefault('id_rows', 3)
    bar_plot_args.setdefault('label_rotation', None)
    bar_plot_args.setdefault('y_label_rotation', None)

    print(f"Highligh: {resolve_highlight(to_plot.ranking_sorted, bar_plot_args['highlight'])}")


    fig1, ax1 = render_bar_plot(
        to_plot,
        fig=plt.figure(dpi=600.0, layout="constrained"),
        **bar_plot_args
    )

    fig1.savefig(str(data_dir.root_dir.absolute() / f"big_image_{marker}.png"))
    print(f"Plotted: big_image_{marker}.png")

    if line_plot_args is None:
        line_plot_args = LinePlotKWArgs()


    line_plot_args.setdefault('targets', resolve_highlight(to_plot.ranking_sorted, bar_plot_args['highlight']))
    line_plot_args.setdefault('colors', None)
    line_plot_args.setdefault('fig_args', dict(
        figsize=(12, 6)
    ))

    fig2, ax2, _, values_odf_the_arrays = render_x_bars(
        to_plot,
        **line_plot_args
    )
    fig2.savefig(str(data_dir.root_dir.absolute() / f"small_image_{marker}.png"))
    print(f"Plotted: small_image_{marker}.png")

    with open(str(data_dir.root_dir.absolute() / f"counts_of_barplot_{marker}.json"), "w") as f:
        json.dump(values_odf_the_arrays, f)

    if not isinstance(generate_Excel, bool) or generate_Excel:

        targets: list[int] = resolve_highlight_to_idx(to_plot.ranking_sorted, bar_plot_args['highlight'])

        print("Exporting excel!")
        original = data_dir.load_original_py_model()
        __targ = [data_dir.load_single(to_plot.ranking_sorted[t].name_no_star) for t in targets]
        __targ_names = [to_plot.ranking_sorted[t].name for t in targets]
        topic_wise_rows = []
        topic_wise_rows_concat = []

        if isinstance(generate_Excel, tuple):
            pass
        elif not isinstance(generate_Excel, bool):
            generate_Excel = (generate_Excel, )
        else:
            generate_Excel = tuple(value for value in range(original.k))
        print(generate_Excel)

        for k in generate_Excel:
            rows = []
            rows_concat = []
            x = list(enumerate(original.get_words_of_topic_sorted(k)))
            print(f"Generate data for origin topic {k}")
            for i, value in x[:100]:
                rows.append((i, [value]))
                rows_concat.append((i, [(value[1], [value])]))

            print(f"Generate data for targets topic {k}")
            for target in __targ:
                print(f"  Generate for {target.name}")
                x2: list[tuple[str, float]] = list(filter(lambda x3: ' ' not in x3[0], target.model_cached.get_words_of_topic_sorted(k)))
                for u, row in zip(x2[:100], rows):
                    row[1].append(u)

                x4: list[tuple[float, list[tuple[str, float]]]] = [v for _, v in itertools.takewhile(lambda x: x[0] < 101, enumerate(chunk_by(lambda value: value[1], x2)))]

                for u, row in zip(x4[:100], rows_concat):
                    row[1].append(u)


            topic_wise_rows.append((k, rows))
            topic_wise_rows_concat.append((k, rows_concat))

        for target in __targ:
            target.uncache_model()

        print("Generate data to write pt1!")
        result1 = []
        result2 = []
        for k, topic_rows in topic_wise_rows:
            print(f"  Generate for topic {k}")
            topic = [f' & $T_{{en}}$ & {' & '.join(__targ_names)}']
            topic2 = [f' & $T_{{en}}$ & {' & '.join(__targ_names)}']
            for i, row in topic_rows:
                topic.append(f'{i} & ' + ' & '.join(f'{{{r[0]}\\\\({r[1]:.5f})}}' for r in row))
                topic2.append(f'{i} & ' + ' & '.join(f'{r[0]}' for r in row))
            result1.append((k, "\\\\\n".join(topic)))
            result2.append((k, "\\\\\n".join(topic2)))

        print("Generate data to write pt2!")
        result3 = []
        result4 = []
        for k, topic_rows_concat in topic_wise_rows_concat:
            print(f"  Generate for topic {k}")
            topic = [f' & $T_{{en}}$ & {' & '.join(__targ_names)}']
            topic2 = [f' & $T_{{en}}$ & {' & '.join(__targ_names)}']
            for i, row_conc in topic_rows_concat:
                s = f'{i}'
                s2 = f'{i}'
                for p, row_conc_entry in row_conc:
                    words = []
                    for w, _ in row_conc_entry:
                        words.append(w)
                    words_s = '\\\\'.join(words)
                    s += f' & {{{words_s}\\\\({p:.5f})}}'
                    s2 += f' & {{{words_s}}}'
                topic.append(s)
                topic2.append(s2)
            result3.append((k, "\\\\\n".join(topic)))
            result4.append((k, "\\\\\n".join(topic2)))

        print("Start writing!")
        with (data_dir.root_dir / f"{marker}_output.txt").open(encoding="utf-8", mode="w") as f:
            for pos, res in enumerate((result1, result2, result3, result4)):
                print("", file=f)
                model_desc = f"# MODEL_TYPE: {pos} #"
                sur = '#'*len(model_desc)
                print(sur, file=f)
                print(model_desc, file=f)
                print(sur, file=f)
                for i, r in res:
                    print("", file=f)
                    print(f'MODEL_TYPE: {pos} - Topic {i}:', file=f)
                    print("...", file=f)
                    print(r, file=f)
                    print("------", file=f)


    if clean_translation:
        data_dir.rm_translated_topic_models()

    data_dir.mark_as_finished()

    return data_dir


_TestIdType = typing.Iterable[int] | float | Fraction | str | Path | os.PathLike


class DictionaryKwArgs(TypedDict, total=True):
    name_suffix: str

class PipelineError(Exception):
    def __init__(self, sub_errors: list[tuple[str, DefectModelError]], payload: dict[str, DataDirectory]):
        self.sub_errors = sub_errors
        self.payload = payload


def run_pipeline(
        experiment_name: str,
        lang_a: LanguageHint | str,
        lang_b: LanguageHint | str,
        data_path: Path | PathLike | str,
        root_dir: Path | PathLike | str,
        original_dictionary_path: str | PathLike | Path,
        dictionary_file_name: str,
        mode: str,
        test_ids: _TestIdType | tuple[_TestIdType, int],
        processor_kwargs: PyAlignedArticleProcessorKwArgs,
        token_filter: TokenCountFilter | None = None,
        tmp_folder: None | Path | PathLike | str = None,
        iters: int|None = None,
        deepl: bool = False,
        translate_mode: typing.Literal["simple", "complex"] = "simple",
        mark_baselines: bool = False,
        generate_Excel: bool | int | tuple[int, ...] = False,
        coocurences_kwargs: CoocurrencesKwArgs | bool = False,
        ndcg_kwargs: NDCGKwArgs | None = None,
        bar_plot_args: BarPlotKWArgs | None = None,
        line_plot_args: LinePlotKWArgs | None = None,
        pipeline_kwargs: DictionaryKwArgs | None = None,
        configs: typing.Iterable[TranslationConfig] | Callable[[], typing.Iterable[TranslationConfig]] | None = None,
        config_modifier: Callable[[TranslationConfig, PyTopicModel, PyDictionary], PyTranslationConfig] | None = None,
        clean_translations: bool = False,
        skip_if_finished_marker_set: bool = True,
        shared_dir: Path | PathLike | str | None = None,
        ngram_statistics: Path | PathLike | str | None | PyNGramStatistics = None,
        min_not_nan: int | float | None = None,
) -> dict[str, DataDirectory]:
    """

    :param skip_if_finished_marker_set:
    :param lang_a:
    :param lang_b:
    :param data_path:
    :param root_dir:
    :param original_dictionary_path:
    :param dictionary_file_name:
    :param mode:
    :param test_ids:
    :param processor_kwargs:
    :param token_filter:
    :param tmp_folder:
    :param iters:
    :param deepl:
    :param translate_mode:
    :param mark_baselines:
    :param generate_Excel:
    :param coocurences_kwargs:
    :param ndcg_kwargs:
    :param bar_plot_args:
    :param line_plot_args:
    :param pipeline_kwargs:
    :param configs:
    :param config_modifier: Allows to modify the config before building it.
    :param clean_translations:
    :param global_model:
    :param ngram_statistics:
    :return:
    """

    if isinstance(lang_a, str):
        lang_a = str(LanguageHint(lang_a))
    else:
        lang_a = str(lang_a)

    if isinstance(lang_b, str):
        lang_b = str(LanguageHint(lang_b))
    else:
        lang_b = str(lang_b)

    if configs is None:
        configs = create_configs

    processor_kwargs.setdefault("lang_a", lang_a)
    processor_kwargs.setdefault("lang_b", lang_b)

    root_dir = root_dir if isinstance(root_dir, Path) else Path(root_dir)
    root_dir.mkdir(parents=True, exist_ok=True)

    if shared_dir is None:
        big_data_gen_path = root_dir
    else:
        shared_dir = Path(shared_dir)
        big_data_gen_path = shared_dir

    processed_phrase_data, docs_phrases, processed_data, docs, docs_filtered, docs_filtered_phrase = None, None, None, None, None, None
    if pipeline_kwargs is not None:
        target_name = pipeline_kwargs["name_suffix"]
        if not target_name.startswith("_"):
            target_name = '_' + target_name
    else:
        target_name = ''

    result_dicts = {}

    for t in mode:
        match t:
            case "p":
                processed_phrase_data = big_data_gen_path / "processed_data_phrases.bulkjson"
                docs_phrases = DataDirectory(root_dir / (experiment_name or ".") / f"paper_phrases{target_name}", shared_dir)
                if skip_if_finished_marker_set and docs_phrases.is_finished():
                    print("Skip finished marker set")
                    result_dicts['p'] = docs_phrases
                    docs_phrases = None
            case "n":
                if processed_data is None:
                    processed_data = big_data_gen_path / "processed_data.bulkjson"
                docs = DataDirectory(root_dir / (experiment_name or ".") / f"paper_no_phrases{target_name}", shared_dir)

                if skip_if_finished_marker_set and docs.is_finished():
                    print("Skip finished marker set")
                    result_dicts['n'] = docs
                    docs = None

            case "f":
                if processed_data is None:
                    processed_data = big_data_gen_path / "processed_data.bulkjson"
                docs_filtered = DataDirectory(root_dir / (experiment_name or ".") / f"paper_filtered_dic{target_name}", shared_dir)
                if skip_if_finished_marker_set and docs_filtered.is_finished():
                    print("Skip finished marker set")
                    result_dicts['f'] = docs_filtered
                    docs_filtered = None
            case "m":
                if processed_data is None:
                    processed_data = big_data_gen_path / "processed_data.bulkjson"
                docs_filtered_phrase = DataDirectory(root_dir / (experiment_name or ".") / f"paper_filtered_dic_no_phrases{target_name}", shared_dir)
                if skip_if_finished_marker_set and docs_filtered_phrase.is_finished():
                    print("Skip finished marker set")
                    result_dicts['m'] = docs_filtered_phrase
                    docs_filtered_phrase = None
            case _:
                raise ValueError(f"{t} not supported")

    if skip_if_finished_marker_set and docs_phrases is None and docs is None and processed_data is None and docs_filtered_phrase is None:
        print("All finished, skipping.")
        return result_dicts

    if big_data_gen_path is not None:
        big_data_gen_path.mkdir(exist_ok=True, parents=True)

    root_dir.mkdir(exist_ok=True, parents=True)

    data_path = data_path if isinstance(data_path, Path) else Path(data_path)

    dictionary = make_dictionary(
        lang_a,
        lang_b,
        original_dictionary_path,
        big_data_gen_path/dictionary_file_name,
        data_path,
        processed_phrase_data,
        processed_data,
        processor_kwargs,
        tmp_folder=tmp_folder,
        token_filter=token_filter,
    )

    if ngram_statistics is not None:
        if isinstance(ngram_statistics, PyNGramStatistics):
            ngram_statistics = ngram_statistics
        else:
            ngram_statistics = PyNGramStatistics.load(ngram_statistics)
    else:
        ngram_statistics = None

    print("Created dict and data!")

    if isinstance(test_ids, tuple):
        test_ids, limit = test_ids
    else:
        limit = None

    if isinstance(test_ids, str):
        if (p := Path(test_ids)).exists():
            try:
                if limit is not None:
                    it = itertools.islice(read_aligned_parsed_articles(p, True), limit)
                else:
                    it = read_aligned_parsed_articles(p, True)
                test_ids = [value.article_id for value in it]
            except Exception:
                if limit is not None:
                    it = itertools.islice(read_aligned_parsed_articles(p), limit)
                else:
                    it = read_aligned_parsed_articles(p)
                test_ids = [value.article_id for value in it]
        print("Loaded test data!")


    args = _RunSingleKWArgs(
        original_data_path=data_path,
        processor=create_processor(**processor_kwargs),
        inp=processed_data,
        test_ids=test_ids,
        token_filter=token_filter,
        iters=iters,
        lang_a=lang_a,
        lang_b=lang_b,
        dictionary=dictionary,
        limit=limit,
        deepl=deepl,
        translate_mode=translate_mode,
        mark_baselines=mark_baselines,
        generate_Excel=generate_Excel,
        ndcg_kwargs=ndcg_kwargs,
        bar_plot_args=bar_plot_args,
        line_plot_args=line_plot_args,
        coocurences_kwargs=coocurences_kwargs,
        stop_words=None,
        filters=None,
        configs=configs,
        config_modifier=config_modifier,
        clean_translation=clean_translations,
        skip_if_finished_marker_set=skip_if_finished_marker_set,
        ngram_statistics=ngram_statistics,
        min_not_nan=min_not_nan
    )

    error = []

    if docs is not None:
        try:
            docs = run_single(
                "no_phrases",
                docs,
                **args
            )
        except DefectModelError as e:
            error.append(("no_phrases", e))

    if docs_filtered is not None:
        def _filter_a1(word: str, _: LoadedMetadataEx | None) -> bool:
            if word.count(' ') > 1:
                return False
            if any(x in word for x in "(){}[].,;:_-#+*/\\1234567890"):
                return False
            return True

        def _filter_a2(word: str, meta: LoadedMetadataEx | None) -> bool:
            assoc = list(meta.associated_dictionaries())
            if not _filter_a1(word, meta):
                return False
            if assoc is None or len(assoc) == 0:
                return True
            if len(assoc) == 1:
                return assoc[0] != "iate" and assoc[0] != "ms_terms"
            if len(assoc) == 2:
                return all(x == "iate" or x == "ms_terms" for x in assoc)
            return True

        args_copy = dict(args)
        args_copy["filters"] = ((_filter_a1, _filter_a1), (_filter_a2, _filter_a2))
        try:
            docs_filtered = run_single("filtered_dict", docs_filtered, **args_copy)
        except DefectModelError as e:
            error.append(("filtered_dict", e))

    if docs_filtered_phrase is not None:
        def _filter_a1(word: str, _: LoadedMetadataEx | None) -> bool:
            if ' ' in word:
                return False
            if any(x in word for x in "(){}[].,;:_-#+*/\\1234567890"):
                return False
            return True

        def _filter_a2(word: str, meta: LoadedMetadataEx | None) -> bool:
            assoc = list(meta.associated_dictionaries())
            if not _filter_a1(word, meta):
                return False
            if assoc is None or len(assoc) == 0:
                return True
            if len(assoc) == 1:
                return assoc[0] != "iate" and assoc[0] != "ms_terms"
            if len(assoc) == 2:
                return all(x == "iate" or x == "ms_terms" for x in assoc)
            return True

        args_copy = dict(args)
        args_copy["filters"] = ((_filter_a1, _filter_a1), (_filter_a2, _filter_a2))
        try:
            docs_filtered_phrase = run_single("filtered_dict_no_phrase", docs_filtered_phrase, **args_copy)
        except DefectModelError as e:
            error.append(("filtered_dict_no_phrase", e))

    if docs_phrases is not None:
        args_copy = dict(args)
        args_copy["processor"] = create_processor(**processor_kwargs, phrases_a=dictionary.voc_a, phrases_b=dictionary.voc_b)
        try:
            docs_phrases = run_single(
            "phrases",
                docs_phrases,
                **args_copy
            )
        except DefectModelError as e:
            error.append(("phrases", e))



    if docs_phrases is not None:
        result_dicts['p'] = docs_phrases
    if docs is not None:
        result_dicts['n'] = docs
    if docs_filtered is not None:
        result_dicts['f'] = docs_filtered
    if docs_filtered_phrase is not None:
        result_dicts['m'] = docs_filtered_phrase
    if len(error) > 0:
        raise PipelineError(error, result_dicts)
    return result_dicts
