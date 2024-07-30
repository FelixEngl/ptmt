import io
from pathlib import Path
from typing import Iterator

from ptmt.dictionary_readers.v1.language import LanguagePair
from ptmt.toolkit.paths import PathObj
from ptmt.dictionary_readers.v1.entries import DictionaryEntrySlim
import tarfile

def _redint(f, b2a: bool = False) -> Iterator[tuple[str, str]]:
    for x in f:
        spl = tuple(y.strip() for y in x.split(' '))
        if len(spl) == 1:
            spl = tuple(y.strip() for y in x.split('\t'))
        if b2a:
            spl = tuple(reversed(spl))
        assert len(spl) == 2, str(spl)
        yield DictionaryEntrySlim(*spl)


def muse_impl(direction: LanguagePair, data_path: PathObj) -> Iterator[DictionaryEntrySlim]:
    if not isinstance(data_path, Path):
        data_path = Path(data_path)
    data_path = data_path / 'MUSE' / 'dictionaries.tar.gz'
    if not data_path.exists():
        raise FileNotFoundError(f'File {data_path} does not exist!')
    with tarfile.open(data_path, mode='r:gz') as tar:
        target = tar.extractfile(f"dictionaries/{direction.langA.language}-{direction.langB.language}.txt")
        if target is not None:
            with io.TextIOWrapper(target, encoding='UTF-8') as f:
                yield from _redint(f)
        target = tar.extractfile(f"dictionaries/{direction.langB.language}-{direction.langA.language}.txt")
        if target is not None:
            with io.TextIOWrapper(target, encoding='UTF-8') as f:
                yield from _redint(f, True)


if __name__ == '__main__':
    for x in muse_impl(LanguagePair.create("en", "de"), r'../../data/MUSE/dictionaries.tar.gz'):
        print(x)
        input()
