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

import os
import typing
from array import array
from collections import defaultdict
from pathlib import Path

import jsonpickle
from _tomotopy import LDAModel
from gensim.models import CoherenceModel
from ldatranslate import PyTopicModel
from tomotopy.utils import Corpus

from ptmt.research.protocols import TranslationConfig

Rating = list[tuple[int, list[tuple[int, float]]]]
"""
[(doc_id, [(topic_id, probability)])]
"""

NDCG = tuple[
    dict[int, tuple[list[float], None | dict[int, int | float] | list[int]]],
    list[int] | None,
    list[int] | None
]
"""
({doc_id, [topic_id]}, [doc_id] | None, [doc_id] | None)
"""


class CoherencesDir:
    def __init__(self, root_dir: Path):
        self._root_dir = root_dir
        self._root_dir.mkdir(exist_ok=True, parents=True)

    @property
    def root_dir(self) -> Path:
        return self._root_dir

    def coherence_path(self, name: str) -> Path:
        return self._root_dir / (name + ".bin")

    def save_coherence(self, name: str, model: CoherenceModel | float):
        path = self.coherence_path(name)
        if isinstance(model, CoherenceModel):
            model.save(str(path.absolute()))
            return
        success = False
        with path.open('wb') as f:
            if not isinstance(model, float):
                print(f"{model} {type(model)} is not a float!")
                model = float(model)
            f.write(b"!#VALUE")
            array('d', [float(model)]).tofile(f)
            success = True
        if not success:
            path.unlink()


    def save_coherences(self, coherences: dict[str, CoherenceModel]):
        for k, v in coherences.items():
            self.save_coherence(k, v)


    def exists(self, name: str) -> bool:
        return self.coherence_path(name).exists()

    def load_coherence(self, name: str) -> float | CoherenceModel | None:
        path = self.coherence_path(name)
        if path.exists():
            with path.open('rb') as f:
                if b"!#VALUE" == f.read(len(b"!#VALUE")):
                    arr = array('d')
                    arr.frombytes(f.read())
                    ret_val = arr[0]
                    del arr
                    return ret_val
            return CoherenceModel.load(str(path.absolute()))
        return None

    def load_coherences(self) -> dict[str, float | CoherenceModel]:
        result = dict()
        for file in self._root_dir.iterdir():
            result[file.stem] = self.load_coherence(file.stem)
        return result

class LazyLoadingEntry:

    def __init__(
            self,
            path: Path,
            model_name: str = "translated_lda.bin",
            config_name: str = "config.json",
            ratings_name: str = "ratings.json",
            ndcg_name: str = "ndcg.json",
            parent = None
    ):
        path.mkdir(exist_ok=True, parents=True)
        self.path = path
        self._coherences = CoherencesDir(self.path / "coherences")
        self._model_path = model_name
        self._model = None
        self._config_path = config_name
        self._config = None
        self._rating_path = ratings_name
        self._rating = None
        self._ndcg_path = ndcg_name
        self._ndcg = None
        self._parent = parent

    @property
    def name(self) -> str:
        return self.path.name


    @property
    def model_path(self) -> Path:
        return self.path / self._model_path

    @property
    def model_cached(self) -> PyTopicModel:
        """
        May cause out of memory, use with care!
        """
        if self._model is None:
            self._model = PyTopicModel.load_binary(self.model_path)
        return self._model

    @property
    def model_uncached(self) -> PyTopicModel:
        if self._model is not None:
            return self._model
        return PyTopicModel.load_binary(self.model_path)

    def uncache_model(self):
        self._model = None

    @property
    def config_path(self) -> Path:
        return self.path / self._config_path


    @property
    def config(self) -> TranslationConfig | None:
        if not self.config_path.exists():
            return None
        if self._config is None:
            self._config = jsonpickle.loads(self.config_path.read_text())
        return self._config

    @property
    def rating_path(self) -> Path:
        return self.path / self._rating_path

    @property
    def rating(self) -> Rating:
        if self._rating is None:
            self._rating = tuple(jsonpickle.loads(self.rating_path.read_text()))
        return list(self._rating)

    def rating_uncached(self) -> Rating:
        if self._rating is None:
            return jsonpickle.loads(self.rating_path.read_text())
        return list(self._rating)

    @property
    def ndcg_path(self) -> Path:
        return self.path / self._ndcg_path

    @property
    def ndcg(self) -> NDCG:
        """
        Returns a tuple where:
        0: A dict between the associated key and the ndcg value
        1: the missed ideals
        2: the missed targets
        """
        if self._ndcg is None:
            self._ndcg = jsonpickle.loads(self.ndcg_path.read_text())
        return self._ndcg

    def ndcg_uncached(self) -> NDCG:
        if self._ndcg is None:
            return jsonpickle.loads(self.ndcg_path.read_text())
        return self._ndcg

    def calculate_ndcg_for(self, top_n_weigts: tuple[int, ...], *, save: bool = False, ignore_existing_file: bool = False) -> None | tuple[dict[int, tuple[list[float], None | dict[int, int | float]]], list[int] | None, list[int] | None]:
        if self.ndcg_path.exists() and not ignore_existing_file:
            print("NDCG for {} is already calculated".format(self.name))
            return self.ndcg

        from ptmt.research.evaluation import rating_to_doc_id_to_ranking, calculate_ndcg
        assert len(top_n_weigts) > 0, "Needs at leas one top!"
        if self._parent is None:
            print("No parent!")
            return None
        i_ranking = rating_to_doc_id_to_ranking(self._parent.load_original_rating())
        relevances = dict(
            (k, defaultdict(lambda: 0, dict((x, y) for x, y in zip(v[:len(top_n_weigts)], top_n_weigts)))) for k, v in i_ranking.items())

        ranking = rating_to_doc_id_to_ranking(self.rating)
        ndcg = calculate_ndcg(i_ranking, ranking, relevances)

        if save:
            if self.ndcg_path.exists():
                self.ndcg_path.unlink()
            self.ndcg_path.write_text(jsonpickle.dumps(ndcg))
        self._ndcg = ndcg
        return ndcg

    @property
    def coherences(self) -> CoherencesDir:
        return self._coherences




class DataDirectory:
    def __init__(self, root_dir: Path | str | os.PathLike = "./paper"):
        if not isinstance(root_dir, Path):
            root_dir = Path(root_dir).absolute()
        root_dir.mkdir(parents=True, exist_ok=True)
        (root_dir / "translation").mkdir(parents=True, exist_ok=True)
        self.root_dir = root_dir
        self.model_cache: None | tuple[LDAModel, PyTopicModel] = None
        self._lazy_cache = dict()
        self._corpus = dict()
        self._coherences = CoherencesDir(self.root_dir / "coherences")

    def set_original_models(self, model: PyTopicModel | LDAModel | tuple[PyTopicModel | LDAModel, PyTopicModel | LDAModel] | None, model1: PyTopicModel | LDAModel | None = None):
        if model is None:
            self.model_cache = None
            return
        if model1 is None:
            assert isinstance(model, tuple), "Needs a tuple if this is only single argument"
            model1 = model[1]
            model = model[0]
        if isinstance(model, LDAModel):
            assert isinstance(model1, PyTopicModel), "Needs an tomotopy and py topic model!"
            self.model_cache = (model, model1)
        elif isinstance(model, PyTopicModel):
            assert isinstance(model1, LDAModel), "Needs an tomotopy and py topic model!"
            self.model_cache = (model1, model)

    def original_model_paths_exists(self) -> bool:
        return all(x.exists() for x in self.original_model_paths)

    @property
    def original_model_paths(self) -> tuple[Path, Path]:
        return self.root_dir / "lda_model.tomotopy.bin", self.root_dir / "lda_model.bin"

    @property
    def coherences(self) -> CoherencesDir:
        return self._coherences

    def load_original_models(self) -> tuple[LDAModel, PyTopicModel]:
        if self.model_cache is not None:
            return self.model_cache
        a, b = self.original_model_paths
        new = LDAModel.load(str(a)), PyTopicModel.load_binary(b)
        self.set_original_models(new)
        return new

    def load_original_py_model(self) -> PyTopicModel:
        if self.model_cache is not None:
            return self.model_cache[1]
        return self.load_original_models()[1]


    def corpus_path(self, target_lang: str) -> Path:
        root = self.root_dir / "corpus"
        root.mkdir(parents=True, exist_ok=True)
        return root / (target_lang + ".bin")

    def corpus(self, target_lang: str) -> Corpus | None:
        if target_lang in self._corpus:
            return self._corpus[target_lang]
        path = self.corpus_path(target_lang)
        if path.exists():
            self._corpus[target_lang] = Corpus.load(str(path.absolute()))
            return self._corpus[target_lang]
        return None

    def set_corpus(self, target_lang: str, corpus: Corpus):
        self._corpus[target_lang] = corpus

    def translation_rating_path(self) -> Path:
        return self.root_dir / 'translation/ratings_original.json'

    def load_original_rating(self) -> Rating:
        return jsonpickle.loads((self.root_dir / 'translation/ratings_original.json').read_text())

    def load_single(self, model_id: str) -> LazyLoadingEntry | None:
        d = self.root_dir / 'translation/translations'
        d = d / model_id
        if d in self._lazy_cache:
            return self._lazy_cache[d]
        if not d.exists() and self.deepl_path().name == model_id:
            return self.deepl_if_exists()
        if d.exists() and not d.is_dir():
            raise IOError("Translation directory does exist bus is not a dir!")
        d.mkdir(exist_ok=True, parents=True)
        n = LazyLoadingEntry(d, parent=self)
        self._lazy_cache[d] = n
        return n

    def deepl_path(self) -> Path:
        return self.root_dir / "translation/DL"

    def deepl(self) -> LazyLoadingEntry:
        path = self.deepl_path()
        if path in self._lazy_cache:
            return self._lazy_cache[path]
        path.mkdir(exist_ok=True, parents=True)
        n = LazyLoadingEntry(path, parent=self)
        self._lazy_cache[path] = n
        return n

    def deepl_if_exists(self) -> LazyLoadingEntry | None:
        deepl = self.deepl()
        if deepl.model_path.exists():
            return deepl
        return None

    def iter_all_translations(self, with_deepl: bool = True) -> typing.Iterator[LazyLoadingEntry]:
        d = self.root_dir / 'translation/translations'
        if with_deepl and (deepl := self.deepl_if_exists()) is not None:
            yield deepl
        for value in d.iterdir():
            if value in self._lazy_cache:
                yield self._lazy_cache[value]
            else:
                n = LazyLoadingEntry(value, parent=self)
                self._lazy_cache[value] = n
                yield n

    def unstemm_path(self) -> Path:
        return self.root_dir / "revert_dict.dict"

