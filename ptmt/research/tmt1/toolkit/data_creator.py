import dataclasses
import typing
from os import PathLike
from pathlib import Path

import jsonpickle
from fraction import Fraction
from ldatranslate.ldatranslate import PyTokenizedAlignedArticle, TokenCountFilter, PyStopWords, \
    PyArticle, PyTokenKind, PyAlignedArticleProcessor, read_aligned_parsed_articles, read_aligned_articles, PyToken

from ptmt.research.tmt1.toolkit.codepoint_filter import is_illegal_char


@dataclasses.dataclass(frozen=True, slots=True)
class TokenCollection:
    origin: list[str] = dataclasses.field(default_factory=list)
    tokenized: list[str] = dataclasses.field(default_factory=list)

    def len(self) -> tuple[int, int]:
        return len(self.origin), len(self.tokenized)

    def len_max(self) -> int:
        return max(*self.len())

    def len_min(self) -> int:
        return min(*self.len())

    def __iter__(self):
        return zip(self.origin, self.tokenized)


@dataclasses.dataclass(frozen=True, slots=True)
class TokenizedValue:
    id: int
    entries: dict[str, TokenCollection]


def process_entry(entry: PyTokenizedAlignedArticle, token_filter: TokenCountFilter | None = None, return_only_complete: bool = True, stop_words: dict[str, PyStopWords] | None = None) -> TokenizedValue | None:
    """Can only return none if a filter is set and return_only_complete is true!"""
    data = dict()
    hints = entry.language_hints

    for hint in hints:
        d: PyArticle | tuple[PyArticle, list[tuple[str, PyToken]]] | None = entry[hint]
        assert d is not None
        if isinstance(d, PyArticle):
            continue
        article, tokens = d
        collection = TokenCollection()
        for origin, token in tokens:
            lemma = token.lemma
            if is_illegal_char(lemma):
                continue
            try:
                int(origin)
                continue
            except ValueError:
                pass
            if token.kind != PyTokenKind.Word:
                continue
            if stop_words is not None and (words := stop_words.get(str(hint))) is not None:
                if origin.lower() in words or lemma.lower() in words:
                    continue
            collection.origin.append(origin)
            collection.tokenized.append(lemma)
        if token_filter is not None:
            if collection.len_min() in token_filter and collection.len_max() in token_filter:
                data[str(hint)] = collection
            elif return_only_complete:
                return None
        else:
            data[str(hint)] = collection
    return TokenizedValue(
        entry.article_id,
        data
    )



def create_train_data(
        input_path: Path | PathLike | str,
        output_path: Path | PathLike | str,
        test_ids: typing.Iterable[int] | float | Fraction | str,
        token_filter: TokenCountFilter | None = None,
        fallback: tuple[PyAlignedArticleProcessor, Path] | None = None,
        stop_words: dict[str, PyStopWords] | None = None,
) -> tuple[Path, Path]:
    """train, test"""
    if not isinstance(input_path, Path):
        input_path = Path(input_path)

    if not isinstance(output_path, Path):
        output_path = Path(output_path)

    if isinstance(test_ids, float) or isinstance(test_ids, str):
        test_ids = Fraction(test_ids)

    created_test_data: set[int] = set()
    if isinstance(test_ids, Fraction):
        a = test_ids.numerator
        b = test_ids.denominator
        last = False
    else:
        test_ids = list(test_ids)


    output_path.mkdir(exist_ok=True, parents=True)
    train_data = output_path / "train.bulkjson"
    test_data = output_path / "test.bulkjson"
    if train_data.exists():
        if test_data.exists():
            print(f"Data already exists")
            return train_data, test_data
        train_data.unlink()
    if test_data.exists():
        test_data.unlink()

    with train_data.open("w", encoding="UTF-8", buffering=1024*1024*1024*1) as train_out:
        with test_data.open("w", encoding="UTF-8", buffering=1024*1024*128*2) as test_out:
            ct = 0
            ct_skip = 0
            for entry in read_aligned_parsed_articles(str(input_path)):
                ct += 1
                if ct % 1000 == 0:
                    print(f"Processed {ct} (Filtered: {ct_skip}, Test: {len(created_test_data)}, Train: {ct - ct_skip - len(created_test_data)})")
                if isinstance(test_ids, Fraction):
                    value = process_entry(entry, token_filter, stop_words=stop_words)
                    if value is None:
                        ct_skip += 1
                        continue
                    if a == 0 and b == 0:
                        a = test_ids.numerator
                        b = test_ids.denominator
                    if a != 0 and (last or b == 0):
                        a -= 1
                        train_out.write(jsonpickle.dumps(value) + "\n")
                    elif b != 0 and (not last or a == 0):
                        b -= 1
                        created_test_data.add(value.id)
                        test_out.write(jsonpickle.dumps(value) + "\n")
                    last = not last
                elif isinstance(test_ids, list):
                    if entry.article_id in test_ids:
                        value = process_entry(entry, stop_words=stop_words)
                        created_test_data.add(value.id)
                        test_out.write(jsonpickle.dumps(value) + "\n")
                    else:
                        value = process_entry(entry, token_filter, stop_words=stop_words)
                        if value is None:
                            ct_skip += 1
                            continue
                        train_out.write(jsonpickle.dumps(value) + "\n")
                else:
                    raise AssertionError("Wrong argument for data gen")

            if isinstance(test_ids, list):
                if len(created_test_data) < len(test_ids):
                    print("Repairing test data")
                    if fallback is None:
                        print("No fallback provided but some test data is missing! Continue incomplete!")
                        return train_data, test_data
                    proc, data = fallback
                    proc: PyAlignedArticleProcessor = proc
                    data: Path = data
                    for value in read_aligned_articles(str(data), True):
                        if value.article_id in test_ids and value.article_id not in created_test_data:
                            print(f"Add {value.article_id}")
                            value = process_entry(proc.process(value), stop_words=stop_words)
                            created_test_data.add(value.id)
                            test_out.write(jsonpickle.dumps(value) + "\n")
    return train_data, test_data
