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

import bz2
import glob
import io
import queue
import typing
from os import PathLike
from pathlib import Path
from typing import Iterator
import re
import tarfile

import lxml.etree
import jsonpickle as JP

from ptmt.corpus_extraction.align import align
from ptmt.corpus_extraction.categories import CategorySupplier
from ptmt.corpus_extraction.parallel_wiki.parsed_article import parse
from ptmt.corpus_extraction.parallel_wiki.raw_article import RawArticlePair, extract, IllegalNesting, \
    IllegalPosition, IllegalNumberOfArticles

from split_file_reader import SplitFileReader


def _read_split_tar_wikicomp(path: str | Path | PathLike[str], consumer: typing.Callable[[typing.TextIO | typing.BinaryIO], Iterator[RawArticlePair]]) -> Iterator[RawArticlePair]:
    if not isinstance(path, Path):
        path = Path(path)
    if path.suffix.endswith('bz2'):
        with bz2.open(path, 'rt', encoding='UTF-8', newline='\n') as f:
            yield from consumer(f)
    else:
        with SplitFileReader(glob.glob(str(path.absolute()) + ".*")) as sp:
            with tarfile.open(fileobj=sp, mode="r") as tar:
                with tar.extractfile('wikicomp-2014_deen.xml.bz2') as bz2f:
                    with bz2.open(bz2f, 'rt', encoding='UTF-8', newline='\n') as f:
                        yield from consumer(f)



def _read_split_tar_wikicomp_no_yield(path: str | Path | PathLike[str], consumer: typing.Callable[[typing.TextIO | typing.BinaryIO], None]):
    if not isinstance(path, Path):
        path = Path(path)

    with SplitFileReader(glob.glob(str(path.absolute()) + ".*")) as sp:
        with tarfile.open(fileobj=sp, mode="r") as tar:
            with tar.extractfile('wikicomp-2014_deen.xml.bz2') as bz2f:
                with bz2.open(bz2f, 'rt', encoding='UTF-8', newline='\n') as f:
                    consumer(f)


def read_wikicomp(path: str | Path) -> Iterator[RawArticlePair]:
    return _read_split_tar_wikicomp(path, extract)



def find_to_specific_str(s: str, goto: int = 1, lookbehind: int = 20, lookahead: int = 20):
    def _find_to_specific_str(f: typing.TextIO):
        nonlocal s, goto, lookbehind, lookahead
        cell_enc = False
        last_100_lines = queue.Queue(lookbehind)
        while not cell_enc:
            line = f.readline().strip()
            if last_100_lines.full():
                last_100_lines.get()
            last_100_lines.put(line)
            # noinspection PyTypeChecker
            if s in line:
                goto -= 1
                cell_enc = goto == 0

        while not last_100_lines.empty():
            print(last_100_lines.get())
        print("_" * 100)
        for _ in range(lookahead):
            print(f.readline().strip())

    _read_split_tar_wikicomp_no_yield(
        "Corpus/wikicomp-2014_deen.xml.bz2.tar",
        _find_to_specific_str
    )


# noinspection PyTypeChecker
def read_chunk_wise(path: str | PathLike[str] | Path) -> Iterator[RawArticlePair]:
    """
    Reads the data chunkwise, more robust than the whole thing.
    """
    def _read(f):
        in_pair = False
        col = []
        ct = 0
        while True:
            line = f.readline()

            if len(line) == 0:
                print(f"End reached: {ct} [{f.readline()}]")
                break
            if '<articlePair' in line:
                in_pair = True
            if not in_pair:
                continue
            col.append(line.strip())
            if '</articlePair>' in line:
                s = '\n'.join(col)
                if re.search('="[^"]*<[^">]*"', s) is not None:
                    print(f"Defect attribute in {col[0]}")
                else:

                    try:
                        with io.BytesIO(s.encode('UTF-8')) as u:
                            parsed = extract(u)
                            lst = list(parsed)
                            assert len(lst) == 1
                            ct += 1
                            yield lst[0]
                    except lxml.etree.XMLSyntaxError as error:
                        print(f"Invalid syntax in {col[0]}: {error}")
                    except IllegalNesting as error:
                        print(f'Invalid nesting for {col[0]}: {error}')
                    except IllegalPosition as error:
                        print(f'Invalid position for {col[0]}: {error}')
                    except IllegalNumberOfArticles as error:
                        print(f'Invalid number of articles for {col[0]}: {error}')
                    except Exception as e:
                        for i, x in enumerate(col):
                            print(f"{i + 1}: {x.strip()}")
                        raise e
                in_pair = False
                col.clear()
    yield from _read_split_tar_wikicomp(path, _read)


def extract_wikicomp_into(
        inp: str | PathLike[str] | Path,
        save_path: str | PathLike[str] | Path = 'preprocessed/wikicomp-2014_deen.bulkjson',
        save_path_categories: str | PathLike[str] | Path = 'preprocessed/wikicomp-2014_deen_categories.json',
        reader: typing.Callable[[str | PathLike[str] | Path], Iterator[RawArticlePair]] = read_chunk_wise,
):
    """
    Reads and stores the wikicomp corpus as bulkjson.
    """

    if not isinstance(save_path, Path):
        save_path = Path(save_path)
    if not isinstance(save_path_categories, Path):
        save_path_categories = Path(save_path_categories)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path_categories.parent.mkdir(parents=True, exist_ok=True)
    print(f"Start parsing {inp}")
    cat_sup = CategorySupplier()
    ct_list = 0
    try:
        with open(save_path, 'w', encoding='UTF-8', buffering=200*1024*1024) as f:
            for x in reader(inp):
                parsed = align(parse(x), cat_sup)
                if parsed.is_list:
                    print(f'List: {parsed.article_id}')
                    ct_list += 1
                    if ct_list % 100 == 0:
                        print(f'Count Lists: {ct_list}')
                f.write(f'{JP.dumps(parsed)}\n')
    finally:
        print(save_path_categories)
        cat_sup.save(save_path_categories)
