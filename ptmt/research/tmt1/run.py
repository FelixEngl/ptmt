from os import PathLike
from pathlib import Path

from ldatranslate.ldatranslate import PyStemmingAlgorithm, TokenCountFilter
from matplotlib.pyplot import colormaps

from ptmt.research.helpers.article_processor_creator import PyAlignedArticleProcessorKwArgs
from ptmt.research.plotting.generate_plots import MPLColor
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
        target_folder: Path | PathLike | str,
        path_to_extracted_data: Path | PathLike | str,
        path_to_the_dictionaries: Path | PathLike | str,
        path_to_raw_data: Path | PathLike | str | None = None
):
    path_to_extracted_data = path_to_extracted_data \
        if isinstance(path_to_extracted_data, Path) \
        else Path(path_to_extracted_data)

    if not path_to_extracted_data.exists():
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
            path_to_extracted_data.parent / f"{path_to_raw_data.stem}_categories.json"
        )

    run_pipeline(
        "en",
        "de",
        path_to_extracted_data,
        target_folder,
        path_to_the_dictionaries,
        "my_dictionary.dict",
        "f",
        test_ids,
        default_processor_kwargs,
        TokenCountFilter(50, 1000),
        "E:/tmp",
        1000,
        False,
        mark_baselines=True,
        generate_Excel=True,
        ndcg_kwargs={
            "top_n_weigts": (3, 2, 1)
        },
        line_plot_args=LinePlotKWArgs(
            colors=colormaps.get("prism")
        ),
        bar_plot_args=BarPlotKWArgs(
            highlight=("P5", "G5", "P3", "M3", "C5*", "DL*", "B3*"),
            label_rotation=270,
            y_label_rotation=270,
            y_label_labelpad=20,
            label_colors=color_provider3
        ),
        coocurences_kwargs=CoocurrencesKwArgs(coocurrences=('u_mass', 'c_w2v'))
    )


if __name__ == '__main__':
    print("Hello")
