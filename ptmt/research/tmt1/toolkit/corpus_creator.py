from os import PathLike
from pathlib import Path

import jsonpickle
from ldatranslate.ldatranslate import TokenCountFilter
from tomotopy.utils import Corpus

from ptmt.research.dirs import DataDirectory
from ptmt.research.tmt1.toolkit.data_creator import TokenizedValue


def create_corpus(
        language: str,
        input_path: Path | PathLike | str,
        output: DataDirectory,
        token_filter: TokenCountFilter | None = None,
        corpus_language: str | None = None
) -> Corpus:
    assert language is not None
    corpus_language = corpus_language if corpus_language is not None else language
    assert corpus_language is not None, f'Language is none!'

    if (corpus := output.corpus(corpus_language)) is not None:
        print(f"Loaded Corpus for {corpus_language}")
        return corpus
    if not isinstance(input_path, Path):
        input_path = Path(input_path)

    print("Build corpus!")

    corpus = Corpus()

    with input_path.open("r", encoding="UTF-8") as inp:
        for line in inp:
            loaded: TokenizedValue = jsonpickle.loads(line)
            words = loaded.entries[language].tokenized
            if token_filter is not None and len(words) not in token_filter:
                continue
            corpus.add_doc(loaded.entries[corpus_language].tokenized)
    print(f"Save {corpus_language} to {output.corpus_path(corpus_language)}")
    corpus.save(str(output.corpus_path(corpus_language).absolute()))
    output.set_corpus(corpus_language, corpus)
    return corpus
