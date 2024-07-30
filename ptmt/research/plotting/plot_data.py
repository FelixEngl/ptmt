import dataclasses
import typing
from collections import defaultdict

import numpy
import numpy as np
import numpy.typing as npt

from ptmt.research.dirs import DataDirectory

_T = typing.TypeVar('_T')
_V = typing.TypeVar('_V', covariant=True)
_E = typing.TypeVar('_E', covariant=True)


def convolut(
        scored: typing.Iterable[_E],
        associated_keys: typing.Iterable[_T | _V],
        *,
        key: typing.Callable[[_T], _V] | None = None
) -> dict[_V, list[_E]]:

    """
    Convoluts all elements according to the provided associated_keys.
    If the associated_keys need some kind of preprocessing, you can use the key
    function to extract some value from a single associated key.
    """

    result = dict()
    for k, v in zip(associated_keys, scored):
        if key is not None:
            k = key(k)
        arr = result.get(k, None)
        if arr is None:
            arr = []
            result[k] = arr
        arr.append(v)
    return result


@dataclasses.dataclass(frozen=True, slots=True, repr=True)
class PlotDataEntry:
    idx_origin: int
    name: str
    name_no_star: str
    ndcg_avg: float
    convolution: dict[float, list[tuple[int, float]]]
    is_baseline: bool


class PlotData:
    ndcg_at: int
    """ndcg@"""
    n_relevant: int
    """The number of relevant elements, by default ndcg_at"""
    ranking: list[PlotDataEntry]
    """avg ndcg to name"""
    ranking_sorted: list[PlotDataEntry]
    """avg ndcg to name sorted"""

    @property
    def ndcg_at_idx(self) -> int:
        return self.ndcg_at - 1

    def __init__(self, paper_dir: DataDirectory, ndcg_at: int, n_relevant: int | None = None, mark_baselines: bool = False):
        n_relevant = n_relevant if n_relevant is not None else ndcg_at
        self.ndcg_at = ndcg_at
        self.n_relevant = n_relevant
        original = paper_dir.load_original_rating()
        targets: list[PlotDataEntry] = []
        paper_dir_targets = list(paper_dir.iter_all_translations())
        for i, translation in enumerate(paper_dir_targets):
            ndcg_at_values = [v[0][self.ndcg_at_idx] for v in translation.ndcg[0].values()]
            pos_and_value = list(enumerate(ndcg_at_values))
            assert len(pos_and_value) == len(original)

            if (cfg := translation.config) is not None:
                is_baseline = cfg.is_baseline
            else:
                is_baseline = True

            if is_baseline and mark_baselines:
                name = translation.name + "*"
            else:
                name = translation.name

            data = PlotDataEntry(
                i,
                name,
                translation.name,
                numpy.average(ndcg_at_values),
                defaultdict(
                    list,
                    convolut(
                        pos_and_value,
                        pos_and_value,
                        key=lambda x: x[1]
                    )
                ),
                is_baseline
            )
            targets.append(data)


        self.ranking = targets
        """avg ndcg to name"""
        self.ranking_sorted = [x for x in targets]
        """avg ndcg to name sorted"""
        self.ranking_sorted.sort(key=lambda x: x.ndcg_avg, reverse=True)

        def calculate_true_positive(n_relevant: int, ideal: list[tuple[int, float]],
                                    system: list[tuple[int, float]]) -> int:
            ideal.sort(key=lambda x: x[1], reverse=True)
            system.sort(key=lambda x: x[1], reverse=True)

            ideal = ideal[:n_relevant]
            system = system[:n_relevant]

            ideal_topics = [topic for topic, _prob in ideal]
            system_topics = [topic for topic, _prob in system]

            tp = 0
            fp = 0
            for x in system_topics:
                if x in ideal_topics:
                    tp += 1
                else:
                    fp += 1
            return tp

        names = []
        top_n_eq = []
        for x in range(self.ndcg_at + 1):
            top_n_eq.append([])

        origin_rating = dict(paper_dir.load_original_rating().copy())
        for value in origin_rating.values():
            value.sort(key=lambda x: x[1], reverse=True)

        self.convolution_ndcg: dict[float, list[PlotDataEntry]] = convolut(
            targets,
            targets,
            key=lambda x: x.ndcg_avg,
        )

        for translation in paper_dir_targets:
            convolution = convolut(
                translation.rating,
                (calculate_true_positive(n_relevant, origin_rating[doc_id], rating.copy()) for doc_id, rating in
                 translation.rating)
            )

            if (cfg := translation.config) is not None:
                is_baseline = cfg.is_baseline
            else:
                is_baseline = True

            if is_baseline and mark_baselines:
                name = translation.name + "*"
            else:
                name = translation.name

            names.append(name)
            for k, v in enumerate(top_n_eq):
                found = convolution.get(k, None)
                if found is not None:
                    v.append(len(found))
                else:
                    v.append(0)

        top_n_eq_sorted = [np.array([x[r.idx_origin] for r in self.ranking_sorted]) for x in top_n_eq]
        top_n_eq = [np.array(x) for x in top_n_eq]
        for x in top_n_eq:
            assert len(x.shape) == 1 and x.shape[0] == len(names), f'Shape not equal {x.shape} - {len(names)}!'

        self.names_and_top_n: tuple[list[str], list[npt.NDArray[int]]] = (names, top_n_eq)

        self.names_and_top_n_sorted: tuple[list[str], list[npt.NDArray[int]]] = (
            [names[x.idx_origin] for x in self.ranking_sorted],
            top_n_eq_sorted,
        )
