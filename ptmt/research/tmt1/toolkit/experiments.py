import pprint
from collections import defaultdict
from os import PathLike

import cycler
import numpy as np
from ldatranslate.ldatranslate import PyTopicModel
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from ptmt.dictionary_readers.v1.dictionary_reader_declarations import *
from ptmt.research.dirs import DataDirectory
from ptmt.research.helpers.math import relative_change
from ptmt.research.helpers.unique import filter_unique


def spread_evenly(inp: Path | str | PathLike, oupout: Path | str | PathLike):
    inp = inp if isinstance(inp, Path) else Path(inp)
    oupout = oupout if isinstance(oupout, Path) else Path(oupout)
    temp = []
    c = 0
    with inp.open("r", buffering=1024 * 1024 * 200, encoding="UTF-8") as f:
        ct = 0
        for line in f:

            ct += len(line) + len("\n")
            if ct < 1_000_000:
                temp.append(line)
            else:
                with (oupout/f"part{c}.txt").open("w", buffering=1024 * 1024 * 200, encoding="UTF-8") as o:
                    o.writelines(temp)
                    temp = []
                    ct = 0
                    c += 1
        if ct > 0:
            with (oupout / f"part{c}.txt").open("w", buffering=1024 * 1024 * 200, encoding="UTF-8") as o:
                o.writelines(temp)


def calculate_differences(border: float, values: dict[str, list[tuple[str, float, str, int]]], *compare_to: str):
    smaller_eq = defaultdict(lambda: 0)
    bigger = defaultdict(lambda: 0)
    for k, v in values.items():
        for name, prob, targ, ct in v:
            if float(k) <= border:
                smaller_eq[name] += ct
            else:
                bigger[name] += ct

    print(f"For <= {border}")
    smaller_eq = dict(smaller_eq)
    bigger = dict(bigger)
    pprint.pprint(smaller_eq)
    pprint.pprint(bigger)
    for k, v1 in bigger.items():
        v2 = smaller_eq[k]
        print(f"{k}: {v1} ({v1 / (v1 + v2):%}), {v2} ({v2 / (v1 + v2):%}) , ")
    if compare_to is not None and len(compare_to) > 0:
        for comp in compare_to:
            print(f"Relative change for smaller_eq for {comp}")
            rel_targ = smaller_eq[comp]
            for k, v in smaller_eq.items():
                if k == comp:
                    continue
                relative_change = (v - rel_targ) / rel_targ
                print(f"  {k}: {relative_change} | {v} {rel_targ} {v - rel_targ}")
            print(f"Relative change for bigger for {comp}")
            rel_targ = bigger[comp]
            for k, v in bigger.items():
                if k == comp:
                    continue
                relative_change = (v - rel_targ) / rel_targ
                print(f"  {k}: {relative_change} | {v} {rel_targ} {v - rel_targ}")


def _linegraph2_data(model: PyTopicModel, topic: int, limit: int, steps: int) -> tuple[list[int], list[float]]:
    x, y = [], []
    for i, value in list(enumerate(model.get_words_of_topic_sorted(topic)))[:limit:steps]:
        x.append(i)
        y.append(value[1])
    return x, y


def linegraph2(data_path: DataDirectory, topic: int, *args: str, limit: int = 30, steps: int = 1):
    with plt.style.context({'font.size': 22}):
        fig, axes = plt.subplots()
        fig: plt.Figure
        fig.set_size_inches(20, 12)
        fig.set_dpi(600)
        axes: plt.Axes
        axes.set_prop_cycle(plt.rcParams["axes.prop_cycle"] * cycler.cycler(linestyle=['-', '--', '-.', ':', (0, (3, 5, 1, 5))]))

        axes.plot(*_linegraph2_data(data_path.load_original_py_model(), topic, limit, steps),
                  color='C0', label="original")

        for i, value in enumerate(args):
            axes.plot(*_linegraph2_data(data_path.load_single(value).model_uncached, topic, limit, steps), color=f'C{i+1}', label=value)
        axes.legend(ncols=3)
        axes.set_yscale("log")
        fig.savefig(f"comp_{topic}.svg")


def collect(r: list[tuple[str, float]], *, limit: int | None = None, steps: int | None = None, filter_doublettes: bool = False) -> tuple[list[int] | None, list[float] | None]:
    iterator: typing.Iterator[tuple[int, str, float]]
    iterator = iter((i, value[0], value[1]) for i, value in enumerate(r))
    if filter_doublettes:
        iterator = filter_unique(iterator, key=lambda r: r[2])
    if limit is not None:
        iterator = itertools.islice(iterator, limit + 1)

    try:
        x = next(iterator)
        tmp = (x[0], x[2])
    except StopIteration:
        return None, None

    ct = 0
    x, y = [], []
    for i, _, value in iterator:
        ct += 1
        change = relative_change(value, tmp[1])
        x.append(tmp[0])
        y.append(change)
        tmp = i, value
    if steps is not None and steps > 1:
        print(f"Steppy: {steps}")
        x, y = x[::steps], y[::steps]
    return x, y


def _linegraph3_data(model: PyTopicModel, topic: int, limit: int | None = None, steps: int | None = None, filter_doublettes: bool = False) -> tuple[list[int], list[float]]:
    x, y = collect(model.get_words_of_topic_sorted(topic), limit=limit, steps=steps, filter_doublettes=filter_doublettes)
    return x, [abs(v) for v in y]


def max_out(arr: list[float]) -> list[float]:
    return [max(arr[i:]) for i in range(len(arr))]


def linegraph3(data_path: DataDirectory, topics: int | tuple[int, ...], *args: str, limit: int = 30, steps: int = 1, unique: bool = False, name_suffix: str = '', logarithmic: bool = False ):
    with plt.style.context({'font.size': 22}):
        fig, axes = plt.subplots()
        fig: plt.Figure
        fig.set_size_inches(20, 12)
        fig.set_dpi(600)
        axes.set_prop_cycle(plt.rcParams["axes.prop_cycle"] * cycler.cycler(linestyle=['-', '--', '-.', ':', (0, (3, 5, 1, 5))]))
        axes: Axes
        if logarithmic:
            axes.set_yscale("log")

        axes.set_xlabel("index of probability")
        axes.set_ylabel("relative delta between probabilities (max)")

        if isinstance(topics, int):
            topics = (topics, )

        for topic in topics:
            x, y = _linegraph3_data(data_path.load_original_py_model(), topic, limit, steps, unique)
            y = max_out(y)
            axes.step(np.arange(len(y)), y, color='C0', label=f"original({topic})", where='mid')

            for i, value in enumerate(args):
                x, y = _linegraph3_data(data_path.load_single(value).model_uncached, topic, limit, steps, unique)
                y = max_out(y)
                axes.step(np.arange(len(y)), y, color=f'C{i+1}', label=f"{value}({topic})", where='mid')

        axes.legend(ncols=3)
        if len(name_suffix) != 0 and not name_suffix.startswith("_"):
            name_suffix = '_' + name_suffix
        fig.savefig(f"comp_delta_{topic}{name_suffix}.svg")

