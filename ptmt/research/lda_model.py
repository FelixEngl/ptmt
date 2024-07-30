import os
import sys
import typing
from pathlib import Path

from ldatranslate.convert_tomotopy_lda import tomotopy_to_topic_model
from ldatranslate.ldatranslate import PyTopicModel
from tomotopy import LDAModel
from tomotopy.utils import Corpus

from ptmt.lda.training import create_by_corpus, run_lda, export_tomotopy
from ptmt.corpus_extraction.align import read_aligned_articles
from ptmt.research.dirs import DataDirectory


def generate_lang_a_lda_model(
        aligned_data_path: Path | os.PathLike | str,
        path: Path | os.PathLike | str | None = None,
) -> tuple[LDAModel, PyTopicModel]:
    if path is None:
        path = Path.cwd()
    elif not isinstance(path, Path):
        path = Path(path)
    corpus = Corpus()
    accepted = 0
    overall = 0
    for value in read_aligned_articles(aligned_data_path):
        tokens = value.articles['en'].tokens
        tokens = list(
            filter(
                lambda x: not any(y in "0123456789,.-;:_{[]}()=?\\/*+#~" for y in x),
                tokens
            )
        )
        overall += 1
        assert tokens is not None
        if len(tokens) < 50:
            continue
        accepted += 1
        corpus.add_doc(tokens)
    print(f"Accepted: {accepted}/{overall}")
    mdl: LDAModel = create_by_corpus(corpus)
    run_lda(mdl, path, 1000)
    topic_model: PyTopicModel = tomotopy_to_topic_model(mdl, 'en')
    topic_model.save_binary(path / 'lda_model.bin')
    return mdl, topic_model

def generate_lda_model_test_data(
    aligned_data_path: Path | os.PathLike | str
) -> typing.Iterator[tuple[int, dict[str, list[str]]]]:
    accepted = 0
    overall = 0
    for value in read_aligned_articles(aligned_data_path):
        tokens_en = value.articles['en'].tokens
        tokens_en = list(
            filter(
                lambda x: not any(y in "0123456789,.-;:_{[]}()=?\\/*+#~" for y in x),
                tokens_en
            )
        )
        tokens_de = value.articles['de'].tokens
        tokens_de = list(
            filter(
                lambda x: not any(y in "0123456789,.-;:_{[]}()=?\\/*+#~" for y in x),
                tokens_de
            )
        )
        overall += 1
        assert tokens_en is not None
        if len(tokens_en) < 50 or len(tokens_de) < 50:
            continue
        accepted += 1
        yield (value.article_id, {'en': tokens_en, 'de': tokens_de})


def create_ratings(model: PyTopicModel, alpha: float, gamma: float, documents: typing.Iterable[tuple[int, list[str]]]) -> list[tuple[int, list[tuple[int, float]]]]:
    return [(doc_id, model.get_doc_probability(doc, alpha, gamma)[0]) for doc_id, doc in documents]


def run_lda_impl(mdl: LDAModel, output_path: DataDirectory, iters: None | int = None):
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

    output_path.original_model_paths[0].parent.mkdir(parents=True, exist_ok=True)

    mdl.save(str(output_path.original_model_paths[0]), True)

    for k in range(mdl.k):
        print('Topic #{}'.format(k))
        for word, prob in mdl.get_topic_words(k):
            print('\t', word, prob, sep='\t')

    export_tomotopy(mdl, output_path.original_model_paths[0].parent / "lda_model_original")


