import dataclasses
import math
import pickle
import random
import typing
from collections import defaultdict
from pathlib import Path

import jsonpickle
from numpy.ma.extras import average
from pygad import pygad

from ptmt.experiment2 import create_run
from ptmt.genetic import gene_manager, Gene
from ptmt.research.plotting.plot_data import PlotData
from ptmt.research.tmt1.pipeline import NDCGKwArgs
from ptmt.research.tmt1.run import run


class _RunningAvg:
    def __init__(self):
        self.sum = 0
        self.min = None
        self.max = None
        self.ct = 0

    @property
    def avg(self):
        return self.sum / self.ct

    def append(self, fittness):
        self.sum += fittness
        self.min = fittness if self.min is None else min(self.min, fittness)
        self.max = fittness if self.max is None else max(self.max, fittness)
        self.ct += 1

    def __str__(self):
        return f'({self.ct}, {self.min}, {self.sum/self.ct}, {self.max})'

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.ct == other.ct and self.min == other.min and self.max == other.max and self.sum == other.sum

    def is_better_than(self, other):
        return other.avg < self.avg and other.min < self.min and other.max < self.max

    def is_better_top_than(self, other):
        return other.avg < self.avg and other.max < self.max

    def is_better_avg_than(self, other):
        return other.avg < self.avg


class _GeneWatcher:
    def __init__(self):
        self.values = defaultdict(_RunningAvg)
        self.gene_avg = _RunningAvg()

    def append(self, gene: int | float, fittness):
        self.gene_avg.append(fittness)
        if isinstance(gene, int):
            self.values[gene].append(fittness)
        else:
            if math.isnan(gene):
                self.values[math.nan].append(fittness)
            else:
                self.values[gene].append(fittness)

    def __str__(self):
        s = '{'
        for k, v in self.values.items():
            s += f'\n  {k}: {v}'
        s += "\n}"
        return s

    def __repr__(self):
        return str(self)

    def __len__(self):
        return len(self.values)

    def __eq__(self, other):
        if self.gene_avg != other.gene_avg:
            return False
        if len(self.values) != len(other.values):
            return False
        for k, v in self.values.items():
            if v != other.values[k]:
                return False
        return True

    def get_best_sep(self) -> typing.Any | None:
        current_best = None

        mi, av, ma = None, None, None
        v_mi, v_av, v_ma = None, None, None

        for k, v in self.values.items():
            if v_mi is None:
                v_mi = v.min
                v_av = v.avg
                v_ma = v.max
                mi, av, ma = k, k, k
            else:
                if v_mi < v.min:
                    v_mi = v.min
                    mi = k
                if v_ma < v.max:
                    v_ma = v.max
                    ma = k
                if v_av < v.avg:
                    v_av = v.avg
                    av = k

            if v.is_better_avg_than(self.gene_avg):
                if current_best is None or v.is_better_than(current_best[1]) or v.is_better_top_than(current_best[1]):
                    current_best = k, v


        if current_best is not None:
            return current_best[0]

        if ma - av < av - mi:
            return ma

        if (ma + mi) / 2 < av:
            return av
        return ma



class _GenesWatcher:
    def __init__(self, size: int):
        self.gene = [_GeneWatcher() for _ in range(size)]

    def append(self, gene: Gene, fittness):
        for i, g in enumerate(gene):
            self.gene[i].append(g, fittness)

    def __str__(self):
        s = ''
        for i, g in enumerate(self.gene):
            s += f'Gene {i}:\n  '
            s += '\n  '.join(str(g).splitlines())
            s += "\n"
        return s

    def reset(self):
        self.gene = [_GeneWatcher() for _ in range(len(self.gene))]

    def get_best_value(self, i) -> typing.Any | None:
        return self.gene[i].get_best_sep()

    def len_of(self, i):
        return len(self.gene[i])

    def __eq__(self, other):
        if len(self.gene) != len(other.gene):
            return False
        for a, b in zip(self.gene, other.gene):
            if a != b:
                return False
        return True


parameter_values: _GenesWatcher = _GenesWatcher(len(gene_manager))

def _fitness_func(ga_instance: pygad.GA, solution: Gene, solution_idx) -> float:
    info, cfg = create_run(
        "v3",
        "experiment6",
        "dictionary_20241130_proc3",
        "../data/ngrams/counts_with_proc.bin",
        **gene_manager.gene_to_args(solution),
        clean_translations=True,
        shared_dir=f"../data/experiment3/shared"
    )
    # print(info)
    # fitness = random.random()
    #
    # parameter_values.append(solution, fitness)
    #
    #
    # return fitness

    data = run(**cfg)
    ndcg_kwargs = { "top_n_weigts": (3, 2, 1) }
    if ndcg_kwargs is None:
        ndcg_kwargs: NDCGKwArgs = NDCGKwArgs()
    ndcg_kwargs.setdefault("top_n_weigts", (1, 1, 1))
    ndcg_kwargs.setdefault("save", True)
    ndcg_kwargs.setdefault("ignore_existing_file", False)
    for translation in data.iter_all_translations():
        translation.calculate_ndcg_for(**ndcg_kwargs)
    to_plot = PlotData(data, 3, mark_baselines=True)
    fitness = to_plot.ranking_sorted[0].ndcg_avg

    return fitness


def _mutate_to_best_known(offspring, ga_instance: pygad.GA):
    if random.random() < 0.85:
        return ga_instance.mutation_randomly(offspring)
    for i in range(len(offspring)):
        if random.random() < 0.05:
            if parameter_values.len_of(i) > 1:
                offspring[i] = parameter_values.get_best_value(i)
    return offspring

# def _on_generation(ga_instance: pygad.GA):
#     print("Next Generation")
#     pass

if __name__ == '__main__':

    gene_manager.set_range("horizontal.factor", [0.5, 1.0, 1.5])
    gene_manager.set_range("horizontal.h_alpha", [0.5])
    gene_manager.set_range("horizontal.alpha", [1.0])
    gene_manager.set_values("horizontal.only_positive_boost", [True], is_optional=False)

    gene_manager.set_range("vertical.alpha", [1.0])
    gene_manager.set_range("vertical.factor", [0.5, 1.0, 1.5])
    gene_manager.set_values("vertical.only_positive_boost", [True], is_optional=False)

    gene_manager.set_range("ngram.boost_lang_a.factor", [0.5, 1.0, 1.5])
    gene_manager.set_values("ngram.boost_lang_a.only_positive_boost", [True], is_optional=False)

    gene_manager.set_range("ngram.boost_lang_b.factor", [0.5, 1.0, 1.5])
    gene_manager.set_values("ngram.boost_lang_b.only_positive_boost", [True], is_optional=False)

    print(gene_manager)

    ga = pygad.GA(
        gene_space=gene_manager.gene_space(),
        keep_elitism=2,
        gene_type=gene_manager.gene_type(),
        allow_duplicate_genes=True,
        initial_population=[gene_manager.rnd() for _ in range(0, 10)],
        num_generations=5,
        fitness_func=_fitness_func,
        num_parents_mating=4,
        # on_generation=_on_generation,
        # save_best_solutions=True,
        mutation_type=_mutate_to_best_known
    )

    ga.run()
    ga.summary()

    with open("data.bin", "wb") as f:
        pickle.dump(parameter_values, f)

    print(gene_manager.gene_type())