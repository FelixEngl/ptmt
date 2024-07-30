import abc
import enum
import functools
import io
import typing
import zipfile
from collections import defaultdict
from os import PathLike
from pathlib import Path
from typing import Protocol, TypeVar
import gensim.models
import numpy as np
import pyLDAvis
import tomotopy as tp
import decimal
import numpy.typing as npt

# noinspection PyProtectedMember
from gensim._matutils import dirichlet_expectation, mean_absolute_difference

"""
corpus = tomotopy.Corpus(<Deine Vorverarbeiteten Daten>)
lda_model = tomopy.train_lda(corpus, iterationen=1000)
lda_model_original = SimpleTopicModel(lda_model)

lda_model_original.save("C:/programme.../fr_lda_v1")
translate_config = API.builder()
    .set_path_to_topic_model("C:/programme.../fr_lda_v1")
    .set_path_to_db(".../fr_de.db")
    .set_path_translated_model_output("C:/programme.../fr_lda_v1_translated")
    .set_voting("CombSUM")
    .build()

API.execute(translate_config, store_additional_normalized=True)
lda_topic_model_trans = SimpleTopicModel.load("C:/programme.../fr_lda_v1_translated")
lda_topic_model_trans_norm = SimpleTopicModel.load("C:/programme.../fr_lda_v1_translated/normalized")
"""

_T_contra = TypeVar("_T_contra", contravariant=True)
_PathType = str | PathLike[str] | Path


def _absolute(path: _PathType) -> Path:
    if not isinstance(path, Path):
        path = Path(path)
    return path.absolute()


class SupportsWrite(Protocol[_T_contra]):
    def write(self, __s: _T_contra) -> object: ...


# create a new context for this task
ctx = decimal.Context()

# 20 digits should be enough for everyone :D
ctx.prec = 20


def float_to_str(f):
    """
    Convert the given float to a string,
    without resorting to scientific notation
    """
    d1 = ctx.create_decimal(repr(f))
    return format(d1, 'f')


class CoherenceModelData:
    corpus_texts: list[list[str]]
    dictionary: gensim.corpora.Dictionary
    gensim_corpus: list[list[tuple[int, int]]]

    @classmethod
    @functools.lru_cache(8)
    def create_from(cls, path_or_corpus: _PathType | tp.utils.Corpus) -> 'CoherenceModelData':
        corpus: tp.utils.Corpus = path_or_corpus \
            if isinstance(path_or_corpus, tp.utils.Corpus) \
            else tp.utils.Corpus.load(str(_absolute(path_or_corpus)))

        corpus_texts: list[list[str]] = [[u for u in corpus[x]] for x in range(len(corpus))]
        dictionary = gensim.corpora.Dictionary(corpus_texts)
        gensim_corpus = [dictionary.doc2bow(doc) for doc in corpus_texts]

        return cls(
            corpus_texts,
            dictionary,
            gensim_corpus
        )

    def __init__(self, corpus_texts: list[list[str]], dictionary: gensim.corpora.Dictionary,
                 gensim_corpus: list[list[tuple[int, int]]]):
        self.corpus_texts = corpus_texts
        self.dictionary = dictionary
        self.gensim_corpus = gensim_corpus


LDASaveMode = typing.Literal['plain', 'p', 'deflated', 'd']


class SimpleTopicModel:
    vocabulary: npt.NDArray[str]  # list[str]
    topics: npt.NDArray[npt.NDArray[np.floating]]  # list[list[float]]
    doc_lengths: npt.NDArray[np.int32]  # list[int]
    doc_topic_dists: npt.NDArray[npt.NDArray[np.floating]]  # list[list[float]]
    term_frequency: npt.NDArray[np.int32]  # list[int]

    # Autogen oder spezial
    word2id: dict[str, int]
    gamma_threshold: float
    alpha: float | None

    def __init__(self, *,
                 model: tp.LDAModel | None = None,
                 vocabulary: tuple[str, ...] | None = None,
                 topics: tuple[tuple[float, ...], ...] | None = None,
                 doc_lengths: tuple[int, ...] | None = None,
                 doc_topic_dists: tuple[tuple[float, ...], ...] | None = None,
                 term_frequency: tuple[int, ...] | None = None,
                 alpha: float | None = None,
                 dtype: np.floating = np.float32  # np.float16 .. np.float64
                 ):

        if model is not None:
            vocabulary = tuple(word for word in model.used_vocabs)
            topics = tuple(tuple(float(value) for value in model.get_topic_word_dist(k)) for k in range(0, model.k))
            doc_lengths = tuple(len(doc.words) for doc in model.docs)
            doc_topic_dists = tuple(tuple(float(x) for x in doc.get_topic_dist()) for doc in model.docs)
            term_frequency = tuple(int(x) for x in model.used_vocab_freq)
            alpha = model.alpha
            for topic in topics:
                assert len(topic) == len(vocabulary)
        else:
            assert vocabulary is not None
            assert topics is not None
            assert doc_lengths is not None
            assert doc_topic_dists is not None
            assert term_frequency is not None

        self.vocabulary = np.array(vocabulary, dtype=str)

        self.topics = np.array(
            tuple(np.array(x, dtype=dtype) for x in topics),
            dtype=np.dtype(np.dtype(dtype))
        )

        self.doc_topic_dists = np.array(
            tuple(np.array(x, dtype=dtype) for x in doc_topic_dists),
            dtype=np.dtype(np.dtype(dtype))
        )

        self.doc_lengths = np.array(doc_lengths, dtype=np.int32)
        self.term_frequency = np.array(term_frequency, dtype=np.int32)
        self.alpha = alpha

        self.dtype = dtype
        self.word2id = {k: i for i, k in enumerate(self.vocabulary)}
        self.random_state = gensim.utils.get_random_state(None)
        self.gamma_threshold = 0.0001

    @property
    def k(self) -> int:
        return len(self.topics)

    MODEL_ZIP_PATH = "model.zip"

    class Target(enum.StrEnum):
        DOC_LENGTHS = "doc/doc_lengths.freq"
        DOC_TOPIC_DISTS = "doc/doc_topic_dists.freq"
        VOCABULARY_FREQ = "voc/vocabulary.freq"
        VOCABULARY = "voc/vocabulary.txt"
        MODEL = "model/topic.model"
        VERSION_INFO = "version.info"

    class TM_Output(Protocol):
        @abc.abstractmethod
        def open(self, path: str) -> typing.TextIO:
            ...

        def __enter__(self):
            return self

    class TM_Output_FileSystem(TM_Output):
        def __init__(self, path: Path | PathLike[str] | str):
            if not isinstance(path, Path):
                path = Path(path)
            self._p = path

        def open(self, path: str) -> typing.TextIO:
            p = self._p / path
            if not p.exists():
                p.parent.mkdir(parents=True, exist_ok=True)
                p.touch(exist_ok=True)
            return (self._p / path).open('w', encoding='utf-8')

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    class _TextIO(io.StringIO):
        _z: zipfile.ZipFile

        def __init__(self, z: zipfile.ZipFile, path: str):
            self._z: zipfile.ZipFile = z
            self._p = path
            super().__init__()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self._z.writestr(self._p, self.getvalue().encode(encoding='UTF-8'))
            super().__exit__(exc_type, exc_val, exc_tb)

    class TM_Output_Zip(TM_Output):
        def __init__(self, path: Path | PathLike[str] | str):
            if not isinstance(path, Path):
                path = Path(path)
            self._z = zipfile.ZipFile(path, mode='w')

        def open(self, path: str) -> typing.TextIO:
            return SimpleTopicModel._TextIO(self._z, path)

        def __exit__(self, exc_type, exc_val, exc_tb):
            self._z.close()

    class TM_Input(Protocol):
        @abc.abstractmethod
        def open(self, path: str) -> typing.TextIO:
            ...

        def __enter__(self):
            return self

        @abc.abstractmethod
        def __exit__(self, exc_type, exc_val, exc_tb):
            ...

    class TM_Input_FileSystem(TM_Input):
        def __init__(self, path: Path | PathLike[str] | str):
            if not isinstance(path, Path):
                path = Path(path)
            self._p = path

        def open(self, path: str) -> typing.TextIO:
            return (self._p / path).open('r', encoding='utf-8')

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    class TM_Input_Zip(TM_Input):
        def __init__(self, path: Path | PathLike[str] | str):
            if not isinstance(path, Path):
                path = Path(path)
            self._p = zipfile.ZipFile(path, mode='r')

        def open(self, path: str) -> typing.TextIO:
            return io.TextIOWrapper(self._p.open(path), encoding='UTF-8')

        def __exit__(self, exc_type, exc_val, exc_tb):
            self._p.close()

    def _save_routinr(self, out: TM_Output):
        with out.open(SimpleTopicModel.Target.VOCABULARY) as voc:
            for word in self.vocabulary:
                voc.write(f"{word}\n")

        with out.open(SimpleTopicModel.Target.VOCABULARY_FREQ) as voc:
            for f in self.term_frequency:
                voc.write(f"{float_to_str(f)}\n")

        with out.open(SimpleTopicModel.Target.DOC_LENGTHS) as voc:
            for f in self.doc_lengths:
                voc.write(f"{f}\n")

        with out.open(SimpleTopicModel.Target.DOC_TOPIC_DISTS) as mf:
            for topic in self.doc_topic_dists:
                mf.write(' '.join(float_to_str(x) for x in topic))
                mf.write("\n")

        with out.open(SimpleTopicModel.Target.MODEL) as mf:
            for topic in self.topics:
                mf.write(' '.join(float_to_str(x) for x in topic))
                mf.write("\n")

    def save(self, path: str | Path, mode: LDASaveMode = 'p'):
        if isinstance(path, str):
            path = Path(path)

        path.mkdir(parents=True, exist_ok=True)

        if mode in ('p', 'plain'):
            out = SimpleTopicModel.TM_Output_FileSystem(path)
        else:
            out = SimpleTopicModel.TM_Output_Zip(path / SimpleTopicModel.MODEL_ZIP_PATH)

        with out as o:
            self._save_routinr(o)

    @staticmethod
    def _load_routine(inp: TM_Input) -> 'SimpleTopicModel':
        with inp.open(SimpleTopicModel.Target.VOCABULARY) as voc:
            vocabulary = tuple(x.rstrip() for x in voc.readlines())

        with inp.open(SimpleTopicModel.Target.VOCABULARY_FREQ) as voc:
            term_frequency = tuple(int(x) for x in voc.readlines())

        with inp.open(SimpleTopicModel.Target.DOC_LENGTHS) as voc:
            doc_lengths = tuple(int(x) for x in voc.readlines())

        with inp.open(SimpleTopicModel.Target.MODEL) as mf:
            topics = tuple(tuple(float(value) for value in line.split(' ')) for line in mf.readlines())

        with inp.open(SimpleTopicModel.Target.DOC_TOPIC_DISTS) as mf:
            doc_topic_dists = tuple(tuple(float(value) for value in line.split(' ')) for line in mf.readlines())

        return SimpleTopicModel(
            vocabulary=vocabulary,
            topics=topics,
            term_frequency=term_frequency,
            doc_lengths=doc_lengths,
            doc_topic_dists=doc_topic_dists
        )

    @staticmethod
    def _get_filesys(path: _PathType) -> TM_Input:
        if not isinstance(path, Path):
            path = Path(path)

        if (path / SimpleTopicModel.MODEL_ZIP_PATH).exists():
            inp = SimpleTopicModel.TM_Input_Zip(path / SimpleTopicModel.MODEL_ZIP_PATH)
        else:
            inp = SimpleTopicModel.TM_Input_FileSystem(path)
        return inp

    @staticmethod
    def _load_partial(inp: TM_Input, target: 'SimpleTopicModel.Target') -> npt.NDArray:
        with inp.open(target) as targ:
            match target:
                case SimpleTopicModel.Target.MODEL | SimpleTopicModel.Target.DOC_TOPIC_DISTS:
                    loaded = tuple(
                        np.array(tuple(float(value) for value in line.split(' ')), dtype=np.float32) for line in
                        targ.readlines())
                    return np.array(
                        loaded,
                        dtype=np.dtype(np.dtype(np.float32))
                    )
                case SimpleTopicModel.Target.VOCABULARY_FREQ | SimpleTopicModel.Target.DOC_LENGTHS:
                    loaded = tuple(int(x) for x in targ.readlines())
                    return np.array(loaded, dtype=np.int32)
                case SimpleTopicModel.Target.VOCABULARY:
                    loaded = tuple(x.rstrip() for x in targ.readlines())
                    return np.array(loaded, dtype=str)

    @staticmethod
    def load_partial(path: _PathType, target: 'SimpleTopicModel.Target') -> npt.NDArray:
        with SimpleTopicModel._get_filesys(path) as inp:
            return SimpleTopicModel._load_partial(inp, target)

    @staticmethod
    def load(path: _PathType) -> 'SimpleTopicModel':
        with SimpleTopicModel._get_filesys(path) as inp:
            return SimpleTopicModel._load_routine(inp)

    def visualize(self, output_file: Path | str | PathLike[str]):
        if isinstance(output_file, str):
            output_file = Path(output_file)

        data = pyLDAvis.prepare(
            self.topics,
            self.doc_topic_dists,
            self.doc_lengths,
            self.vocabulary,
            self.term_frequency,
            start_index=0,
            sort_topics=False
        )
        with output_file.open("w", encoding="utf-8") as f:
            pyLDAvis.save_html(
                data,
                f
            )

    def translate(self, words: typing.Iterable[str]) -> list[tuple[str, int | None]]:
        return [(word, self.word2id.get(word, None)) for word in words]

    def get_top_topic_words_iter(self, topic: int) -> typing.Iterator[tuple[str, float]]:
        _sorted = np.flip(np.argsort(self.topics[topic]))
        for value in _sorted:
            yield str(self.vocabulary[value]), float(self.topics[topic][value])

    def get_all_top_topic_words_iter(self) -> list[typing.Iterator[tuple[str, float]]]:
        return [self.get_top_topic_words_iter(k) for k in range(self.k)]

    def get_top_topic_words(self, topic: int, n: int | None = None) -> list[tuple[str, float]]:
        _sorted = np.flip(np.argsort(self.topics[topic]))
        if n is not None:
            _sorted = _sorted[:n]
        return [(str(self.vocabulary[x]), float(self.topics[topic][x])) for x in _sorted]

    def get_all_top_topic_words(self, n: int | None = 10) -> list[list[tuple[str, float]]]:
        return [self.get_top_topic_words(k, n) for k in range(self.k)]

    def summary(self, *, file: SupportsWrite[str] | None = None):
        for topic in range(self.k):
            print(f'Topic #{topic}:', file=file)
            for (word, prob) in self.get_top_topic_words(topic, 10):
                print('\t', word, prob, file=file)
            print('\t', '...', file=file)
            print(file=file)

    def topic_term_dists(self):
        return self.topics.sum(axis=1)
        # return tuple(sum(topic) for topic in self.topics)

    @staticmethod
    def meta_info_exists(target_path: Path) -> bool:
        path_to_visualisation = target_path / 'visualisation.html'
        path_to_summary = target_path / 'summary.txt'
        return path_to_visualisation.exists() and path_to_summary.exists()

    def store_meta_into(self, target_path: Path, override: bool):
        try:
            path_to_visualisation = target_path / 'visualisation.html'
            if path_to_visualisation.exists():
                if not override:
                    print('  RENDER ALREADY EXISTS!')
                    return
                path_to_visualisation.unlink()
            self.visualize(path_to_visualisation)
        except Exception as e:
            print('  FAILED RENDER')
            (target_path / 'FAILED').write_text(str(e))
        with (target_path / 'summary.txt').open('w', encoding='UTF-8', newline='\n') as w:
            self.summary(file=w)

    def topic_as_sorted_strings(self, topic: int) -> list[str]:
        _sorted = np.flip(np.argsort(self.topics[topic]))
        return list(np.array(self.vocabulary)[_sorted])

    def topics_as_sorted_strings(self) -> list[list[str]]:
        return [self.topic_as_sorted_strings(x) for x in range(self.k)]

    @classmethod
    def prepare_coherence_model_data(cls, path_or_corpus: _PathType | tp.utils.Corpus) -> CoherenceModelData:
        return CoherenceModelData.create_from(path_or_corpus)

    def get_word_probability(self, word: str | int, min_probability: float = 1E-10) -> list[tuple[int, float]]:
        if isinstance(word, str):
            word = self.word2id[word]
        min_probability = max(1E-10, min_probability)
        values: list[tuple[int, float]] = []
        for topic_id in range(self.k):
            prob = float(self.topics[topic_id][word])
            if prob >= min_probability:
                values.append((topic_id, prob))
        return values

    def get_doc_probability(
            self,
            doc: typing.Iterable[str] | typing.Iterable[int],
            minimum_probability: float = 1E-10,
            minimum_phi_value: float = 1E-10,
            per_word_topics: bool = False
    ) -> tuple[
        list[tuple[int, float]], None | list[tuple[int, list[int]]], None | list[tuple[int, list[tuple[int, float]]]]]:
        minimum_probability = max(1E-10, minimum_probability)
        minimum_phi_value = max(1E-10, minimum_phi_value)
        if not isinstance(doc, list):
            doc = list(doc)
        bow, missing = self.doc2bow(doc)
        #  bow = [(word_i2, count)...]
        gamma, phis = self.inference([bow], collect_sstats=per_word_topics)
        topic_dist = gamma[0] / sum(gamma[0])  # normalize distribution

        document_topics: list[tuple[int, float]] = [
            (topicid, topicvalue) for topicid, topicvalue in enumerate(topic_dist)
            if topicvalue >= minimum_probability
        ]

        if not per_word_topics:
            return document_topics, None, None

        word_topic: list[tuple[int, list[int]]] = []  # contains word and corresponding topic
        word_phi: list[tuple[int, list[tuple[int, float]]]] = []  # contains word and phi values
        for word_type, weight in bow:
            phi_values: list[tuple[float, int]] = []  # contains (phi_value, topic) pairing to later be sorted
            phi_topic: list[
                tuple[int, float]] = []  # contains topic and corresponding phi value to be returned 'raw' to user
            for topic_id in range(self.k):
                _v = float(phis[topic_id][word_type])
                if _v >= minimum_phi_value:
                    # appends phi values for each topic for that word
                    # these phi values are scaled by feature length
                    phi_values.append((_v, topic_id))
                    phi_topic.append((topic_id, _v))

            # list with ({word_id => [(topic_0, phi_value), (topic_1, phi_value) ...]).
            word_phi.append((word_type, phi_topic))
            # sorts the topics based on most likely topic
            # returns a list like ({word_id => [topic_id_most_probable, topic_id_second_most_probable, ...]).
            sorted_phi_values = sorted(phi_values, reverse=True)
            topics_sorted = [x[1] for x in sorted_phi_values]
            word_topic.append((word_type, topics_sorted))

        return document_topics, word_topic, word_phi  # returns 2-tuple

    def prepare_inference(self, original_model: tp.LDAModel | None = None, /, alpha=None,
                          gamma_threshold: float = None):
        if original_model is not None:
            assert alpha is None
            alpha = original_model.alpha
        self.alpha = alpha
        if gamma_threshold is not None:
            self.gamma_threshold = gamma_threshold

    def doc2bow(self, doc: list[str] | list[int]) -> tuple[list[tuple[int, int]], dict[str, int] | None]:
        doc_clean = []
        for x in doc:
            if isinstance(x, str):
                doc_clean.append(self.word2id.get(x, x))
            else:
                doc_clean.append(x)
        cts = defaultdict(lambda: 0)
        fallback = defaultdict(lambda: 0)
        for word in doc_clean:
            if isinstance(word, str):
                fallback[word] += 1
            else:
                cts[word] += 1

        if len(fallback) == 0:
            fallback = None

        return [(k, v) for k, v in cts.items()], fallback

    def inference(
            self,
            chunk: list[list[tuple[int, int]]],
            collect_sstats: bool = False,
            iterations: int = 1000
    ):
        gamma = self.random_state.gamma(100., 1. / 100., (len(chunk), self.k)).astype(self.dtype, copy=False)
        e_log_theta = dirichlet_expectation(gamma)
        exp_e_log_theta = np.exp(e_log_theta)
        # print(exp_e_log_theta.shape)

        assert e_log_theta.dtype == self.dtype
        assert exp_e_log_theta.dtype == self.dtype

        if collect_sstats:
            sstats = np.zeros_like(self.topics)
            # print(sstats.shape)
        else:
            sstats = None
        converged = 0
        integer_types = (int, np.integer,)
        epsilon = np.finfo(self.dtype).eps

        for d, doc in enumerate(chunk):
            if len(doc) > 0 and not isinstance(doc[0][0], integer_types):
                ids = [int(idx) for idx, _ in doc]
            else:
                ids = [idx for idx, _ in doc]
            cts = np.fromiter((cnt for _, cnt in doc), dtype=self.dtype, count=len(doc))
            gamma_d = gamma[d, :]
            # e_log_theta = e_log_theta[d, :]
            exp_e_log_theta_d = exp_e_log_theta[d, :]
            exp_e_log_beta_d = self.topics[:, ids]
            phinorm = np.dot(exp_e_log_theta_d, exp_e_log_beta_d) + epsilon

            for _ in range(iterations):
                lastgamma = gamma_d
                gamma_d = self.alpha + exp_e_log_theta_d * np.dot(cts / phinorm, exp_e_log_beta_d.T)

                e_log_theta_d = dirichlet_expectation(gamma_d)
                exp_e_log_theta_d = np.exp(e_log_theta_d)
                phinorm = np.dot(exp_e_log_theta_d, exp_e_log_beta_d) + epsilon
                meanchange = mean_absolute_difference(gamma_d, lastgamma)
                if meanchange < self.gamma_threshold:
                    converged += 1
                    break
            gamma[d, :] = gamma_d
            assert gamma_d.dtype == self.dtype
            if collect_sstats:
                # Contribution of document d to the expected sufficient
                # statistics for the M step.
                sstats[:, ids] += np.outer(exp_e_log_theta_d.T, cts / phinorm)

        if collect_sstats:
            # This step finishes computing the sufficient statistics for the
            # M step, so that
            # sstats[k, w] = \sum_d n_{dw} * phi_{dwk}
            # = \sum_d n_{dw} * exp{Elogtheta_{dk} + Elogbeta_{kw}} / phinorm_{dw}.
            sstats *= self.topics
            assert sstats.dtype == self.dtype

        assert gamma.dtype == self.dtype
        return gamma, sstats

    @classmethod
    def calculate_metrics(
            cls,
            path_to_model: _PathType,
            path_or_corpus_or_data: _PathType | tp.utils.Corpus | CoherenceModelData,
            topn: int = 20,
            window_size: int | None = None,
    ) -> dict[str, gensim.models.CoherenceModel]:
        lda_a = SimpleTopicModel.load(path_to_model)
        if isinstance(path_or_corpus_or_data, CoherenceModelData):
            data = path_or_corpus_or_data
        else:
            data = CoherenceModelData.create_from(path_or_corpus_or_data)

        return {x: gensim.models.CoherenceModel(
            topics=lda_a.topics_as_sorted_strings(),
            texts=data.corpus_texts,
            dictionary=data.dictionary,
            corpus=data.gensim_corpus,
            topn=topn,
            coherence=x,
            window_size=window_size,
        ) for x in ('u_mass', 'c_v', 'c_uci', 'c_npmi', 'c_w2v')}

