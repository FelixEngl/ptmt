import math
import typing
from collections import defaultdict

from ptmt.genetic import Gene


class RunningAvg:
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


class GeneWatcher:
    def __init__(self):
        self.values = defaultdict(RunningAvg)
        self.gene_avg = RunningAvg()

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



class GenesWatcher:
    def __init__(self, size: int):
        self.gene = [GeneWatcher() for _ in range(size)]

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
        self.gene = [GeneWatcher() for _ in range(len(self.gene))]

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
