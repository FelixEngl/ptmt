from os import PathLike
from pathlib import Path

from _tomotopy import LDAModel
from ldatranslate.convert_tomotopy_lda import tomotopy_to_topic_model
from ldatranslate.ldatranslate import TokenCountFilter, PyTopicModel

from ptmt.lda.training import create_by_corpus
from ptmt.research.dirs import DataDirectory
from ptmt.research.lda_model import run_lda_impl
from ptmt.research.tmt1.toolkit.corpus_creator import create_corpus


def train_models(
        language: str,
        input_path: Path | PathLike | str,
        output_path: DataDirectory,
        token_filter: TokenCountFilter | None = None,
        iters: int|None = None
):

    if output_path.original_model_paths_exists():
        print("All models are trained!")
        return

    if iters is None:
        iters = 1000

    corpus = create_corpus(language, input_path, output_path, token_filter)
    mdl: LDAModel = create_by_corpus(corpus)
    run_lda_impl(mdl, output_path, iters)
    topic_model: PyTopicModel = tomotopy_to_topic_model(mdl, language)
    topic_model.save_binary(output_path.original_model_paths[1])
    output_path.set_original_models(mdl, topic_model)
