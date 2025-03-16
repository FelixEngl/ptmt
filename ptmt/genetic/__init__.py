import base64
import inspect
import random
import typing

import math
from pprint import pprint

import numpy as np
from ldatranslate.ldatranslate import *

from ptmt.create.horizontal import HorizontalKwargs
from ptmt.create.vertical import VerticalKwargs
from ptmt.create.ngram import NGramBoostKwargs, NGramLanguageBoostKwargs


GeneRange = range | typing.Sequence[int | float] | dict[str, int | float]
Gene = typing.MutableSequence[int | float]

class GeneDescriptor:
    def __init__(
            self,
            position: int,
            is_optional: bool,
            is_enum: bool,
            values: list[tuple[str, typing.Any] | typing.Any] | type,
            key: tuple[str, ...],
            optional_sub: bool,
            is_str: bool,
            compatible_types: tuple[type, ...],
    ):
        self.position: int = position
        self._range: GeneRange | None = None
        self._range_nullable: GeneRange | None = None
        self.is_enum = is_enum
        self.optional_sub = optional_sub
        self.original_is_optional = is_optional
        self.is_bool = False
        self.is_str = is_str
        self._base_type_is_float: bool = False
        self._base_type_is_int: bool = False
        self.key: tuple[str, ...] = key
        self.compatible_types: tuple[type, ...] = compatible_types
        self._set_internal(values, is_optional)

    def _set_internal(self,  values: list[tuple[str, typing.Any] | typing.Any] | type, is_optional: bool):
        self.is_optional = is_optional
        if self.is_str:
            self._mapping_ab = []
            self._mapping_ba = {}
            if self.is_optional or self.is_only_nullable_for_filter:
                self._mapping_ab.append(None)
                self._mapping_ba[None] = 0
        elif self.is_enum:
            self._mapping_ab = []
            self._mapping_ba = {}
            if self.is_optional or self.is_only_nullable_for_filter:
                self._mapping_ab.append(None)
                self._mapping_ba[None] = 0
            for value in values:
                i = len(self._mapping_ab)
                self._mapping_ab.append(value)
                self._mapping_ba[value[1]] = i
            self._range = range(0, len(self._mapping_ab))
        else:
            self._base_type_is_float = float == values
            self._base_type_is_int = int == values
            if values == bool or (isinstance(values, list) and all(isinstance(value, bool) for value in values)):
                if isinstance(values, list):
                    self._mapping_ab = sorted(set(values))
                    self._mapping_ba = {}
                    for i, value in enumerate(values):
                        self._mapping_ba[value] = i
                else:
                    self.is_bool = True
                    self._mapping_ba = {
                        False: 0,
                        True: 1,
                    }
                    self._mapping_ab = [False, True]
                if self.is_optional or self.is_only_nullable_for_filter:
                    self._mapping_ba[None] = len(self._mapping_ab)
                    self._mapping_ab.append(None)
            else:
                self._mapping_ab = None
                self._mapping_ba = None
        self.reset_range()

    @property
    def is_only_nullable_for_filter(self) -> bool:
        return not self.original_is_optional and self.optional_sub

    def reset_range(self):
        if self._mapping_ab is None or len(self._mapping_ab) == 0:
            self._range = None
            if self._base_type_is_int:
                self._range_nullable = range(0, 11)
            return
        if self.is_only_nullable_for_filter:
            self._range_nullable = range(0, len(self._mapping_ab))
            if self._mapping_ab[0] is None:
                self._range = range(1, len(self._mapping_ab))
                return
            if self._mapping_ab[-1] is None:
                self._range = range(1, len(self._mapping_ab) - 1)
                return
            new_range = []
            for i, v in enumerate(self._mapping_ab):
                if v is None:
                    continue
                new_range.append(i)
                self._range = new_range
                return
        self._range = range(0, len(self._mapping_ab))

    def is_child_of(self, other: tuple[str, ...]) -> bool:
        if len(self.key) <= len(other):
            return False
        return self.key[:len(other)] == other

    def get_ranges_secure(self) -> GeneRange:
        if self._range is None:
            if self._base_type_is_float:
                return {
                    'low': 0.0,
                    'high': 1.0,
                    'step': 0.1
                }
            if self._base_type_is_int:
                return range(0, 10, 1)
            raise ValueError(f'Missing default range for {self}')
        return self._range


    def set_value(self, value: typing.Any):
        if self.is_enum:
            raise ValueError("Can not add to enum values!")
        if self.is_bool:
            raise ValueError("Can not add to bool values!")
        if self.is_str:
            assert type(value) in self.compatible_types, f'{value} not one of the compatible type {self.compatible_types}!'
            k = len(self._mapping_ab)
            self._mapping_ab.append(value)
            self._mapping_ba[value] = k
        raise ValueError(f"Can not set a value for the type {self.compatible_types}!")

    def can_set_value(self) -> bool:
        return self.is_str

    def set_values(self, values: list[tuple[str, typing.Any] | typing.Any], is_optional: bool | None = None):
        if is_optional is None:
            is_optional = self.is_optional
        if self.is_enum:
            if isinstance(values, list):
                new = []
                for value in values:
                    if isinstance(value, tuple):
                        new.append(value)
                    else:
                        new.append((str(value), value))
                values = sorted(new, key=lambda x: x[0])
        self._set_internal(values, is_optional)

    def set_range(self, r:GeneRange | None):
        if isinstance(r, typing.Sequence) and not (isinstance(r, dict) or isinstance(r, range)):
            r = sorted(r)
        self._range = r

    def base_type(self) -> type:
        return float if self._base_type_is_float else int

    def value_in_range(self, value: int | float) -> bool:
        if math.isnan(value) and self._base_type_is_float:
            return True
        r = self.get_ranges_secure()
        if isinstance(r, dict):
            return r['low'] <= value <= r['high']
        else:
            return value in r

    def gene_is_valid(self, gene: Gene) -> bool:
        if self.is_only_nullable_for_filter:
            if self._range_nullable is not None:
                return gene[self.position] in self._range_nullable
        return self.value_in_range(gene[self.position])

    def is_null(self, value: int | float) -> bool:
        return self.read_single_value_to_args(value)[1] is None

    def read_single_value_to_args(self, value: int | float) -> (tuple[str, ...], typing.Any | None):
        if (self.is_optional or self.is_only_nullable_for_filter) and value == self.null:
            return self.key, None
        if self._base_type_is_float:
            if math.isnan(value):
                return self.key, None
            return self.key, value
        elif self.is_enum:
            v = self._mapping_ab[value]
            if v is None:
                return self.key, None
            return self.key, v[1]
        elif self.is_bool:
            return self.key, self._mapping_ab[value]
        elif self._base_type_is_int:
            if not self.value_in_range(value):
                return self.key, None
            return self.key, value
        else:
            return self.key, self._mapping_ab[value]

    def read_from_gene(self, gene: typing.Sequence[int | float]) -> (tuple[str, ...], typing.Any | None):
        return self.read_single_value_to_args(gene[self.position])

    def _convert_gene_value(self, value: typing.Any) -> int | float:
        if self._base_type_is_float:
            if value is None:
                return math.nan
            return value
        elif self.is_bool or self.is_enum:
            return self._mapping_ba[value]
        elif self.is_str:
            if len(self._mapping_ba):
                return 0
            else:
                return self._mapping_ba[value]
        assert value is not None, f"Failed retrieving {value} for {self}"
        return value

    def get_gene_value(self, args: dict[str, typing.Any]) -> int | float:
        value = args
        for i, p in enumerate(self.key):
            value = value.get(p, None)
            if value is None and i != len(self.key) - 1:
                assert self.optional_sub, f"Something else than a special nullable for filter is not mappable! {self.key}"
                break

        return self._convert_gene_value(value)

    def set_value_from_gene(self, gene: typing.Sequence[int], d: dict[str, typing.Any]) -> dict[str, typing.Any]:
        path, value = self.read_from_gene(gene)
        def set_d_value(target: dict, path, value):
            if len(path) == 1:
                target[path[0]] = value
            else:
                tmp = target.get(path[0], {})
                target[path[0]] = set_d_value(tmp, path[1:], value)
            return target
        return set_d_value(d, path, value)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        s = f'Gene {self.position}:'
        s += f'\n  Key: {self.key}'
        s += f'\n  Original Nullable: {self.original_is_optional}'
        s += f'\n  Optional: {self.is_optional}'
        s += f'\n  Optional Sub: {self.optional_sub}'
        s += f'\n  Nullable for Filter: {self.is_only_nullable_for_filter}'
        s += f'\n  Compatible: {self.compatible_types}'
        s += f'\n  Range: {self._range}'
        if self.is_enum:
            s += f'\n  Enum Values:'
            for i, v in enumerate(self._mapping_ab):
                s += f"\n    {i}: {v},"
        elif self.is_bool:
            s += f'\n  Bool Values:'
            for i, v in enumerate(self._mapping_ab):
                s += f"\n    {i}: {v},"
        elif self._base_type_is_float:
            s += f'\n  Base Type:'
            s += f"\n    FLOAT "
            if self.is_optional:
                s += "(OPT)"
        else:
            s += f'\n  Base Type:'
            s += f"\n    INT "
            if self.is_optional:
                s += "(OPT)"
        return s

    @property
    def null(self) -> int | float | None:
        if self._base_type_is_float:
            return math.nan
        if self.is_bool or self.is_enum or self.is_str:
            return self._mapping_ba.get(None, None)
        if self._base_type_is_int:
            if self._range is not None:
                return self._range.stop + 1
            return 11
        raise ValueError(f"Failed retrieving null for {self}")

    def set_null(self, gene: Gene) -> Gene:
        d = self.null
        if d is None:
            return gene
        gene[self.position] = d
        return gene


    def rnd(self, rnd: random.Random | None = None) -> int | float:
        if rnd is None:
            rnd = random.Random()

        r = None
        if self.is_only_nullable_for_filter:
            r = self._range_nullable
        if r is None:
            r = self._range


        if r is not None:
            if isinstance(r, range):
                if not self._base_type_is_float:
                    return rnd.randrange(r.start, r.stop, r.step)
                return rnd.random() * (r.stop - r.start) + r.start
            if isinstance(r, dict):
                low = r['low']
                high = r['high']
                step = r['step']
                if self._base_type_is_float:
                    def randrange_float(start, stop, step):
                        return rnd.randint(0, round((stop - start) / step)) * step + start
                    return randrange_float(low, high, step)
                else:
                    return rnd.randrange(int(low), int(high), max(1, int(step)))
            else:
                return r[rnd.randrange(0, len(r))]
        if self.is_optional or self.is_only_nullable_for_filter:
            if self._base_type_is_float:
                v = rnd.random() * 1.01
                if v <= 0.01:
                    return math.nan
                return round(v - 0.01, 1)
            if self.is_bool:
                return rnd.randrange(0, 3, 1)
            else:
                return rnd.randrange(0, 11, 1) - 1
        else:
            if self._base_type_is_float:
                return round(rnd.random(), 1)
            if self.is_bool:
                return rnd.randrange(0, 2, 1)
            return rnd.randrange(0, 10, 1)



class GeneKwargs(typing.TypedDict):
    horizontal: typing.NotRequired[HorizontalKwargs]
    vertical: typing.NotRequired[VerticalKwargs]
    ngram: typing.NotRequired[NGramBoostKwargs]


class GeneManager:
    @staticmethod
    def _to_gene_mapping(
            gene_members: type,
            enums: list[type],
            kwargs: list[type],
            *,
            key: tuple[str, ...] = (),
            providers: list[GeneDescriptor] = None,
            optional_sub: bool = False,
            nullable_paths: list[tuple[str, ...]] | None = None,
            sort: bool = False,
    ) -> tuple[list[GeneDescriptor], list[tuple[str, ...]] | None]:
        if providers is None:
            providers = []
        member_fields = inspect.get_annotations(gene_members)

        if sort:
            member_fields = sorted(member_fields.items(), key= lambda x: x[0])
        else:
            member_fields = member_fields.items()

        for name, typ in member_fields:
            curr_key = key + (name, )
            is_str = False
            if isinstance(typ, type):
                is_optional = False
                compatible_types = (typ,)
            else:
                is_optional = True
                args = dict(inspect.getmembers(typ))['__args__']
                assert typ.__origin__.__name__ == 'NotRequired', "Why is it not required?"
                assert len(args) == 1, "Only one optional type supported"
                typ = args[0]
                if not isinstance(typ, type):
                    args = dict(inspect.getmembers(typ))['__args__']
                    if str in args:
                        is_str = True
                    compatible_types = args
                else:
                    compatible_types = (typ, )

            is_enum = False
            if typ in enums:
                enum_members = list(filter(lambda x: not x[0].startswith('_'), inspect.getmembers(typ)))
                enum_members = sorted(enum_members, key=lambda x: x[0])
                values = enum_members
                is_enum = True
            elif typ in kwargs:
                if is_optional:
                    if nullable_paths is None:
                        nullable_paths = []
                    nullable_paths.append(curr_key)
                providers, nullable_paths = GeneManager._to_gene_mapping(
                    typ,
                    enums,
                    kwargs,
                    key=curr_key,
                    providers=providers,
                    optional_sub=is_optional,
                    nullable_paths=nullable_paths,
                    sort=sort
                )
                continue
            else:
                values = typ
            if not is_str:
                is_str = str == typ

            providers.append(
                GeneDescriptor(
                    len(providers),
                    is_optional,
                    is_enum,
                    values,
                    curr_key,
                    optional_sub,
                    is_str,
                    compatible_types
                )
            )
        return providers, nullable_paths

    def __init__(self, gene_members: type, *, enums: list[type] | None = None, kwargs: list[type] | None = None, sort: bool = False):
        if kwargs is None:
            kwargs = []
        if enums is None:
            enums = []
        self.genes, self.nullable_paths = GeneManager._to_gene_mapping(gene_members, enums, kwargs, sort=sort)
        v = set(x.key for x in self.genes)
        assert len(v) == len(self.genes), "Some genes have the same key!!!"
        if self.nullable_paths is not None:
            self.nullable_paths = sorted(self.nullable_paths, key=lambda x: len(x), reverse=True)

    def __str__(self):
        s = '\n'.join(str(value) for value in self.genes)
        if self.nullable_paths is not None:
            s += '\nNullable Paths:\n  '
            s += '\n  '.join('.'.join(x) for x in self.nullable_paths)
        return s

    def set_value(self, key: str | tuple[str, ...], value: typing.Any):
        if isinstance(key, str):
            key = tuple(key.split('.'))
        for v in self.genes:
            if v.key == key:
                v.set_value(value)
                return

    def set_range(self, key: str | tuple[str, ...], value: range | typing.Sequence[int | float] | None | dict[str, typing.Any]):
        if isinstance(key, str):
            key = tuple(key.split('.'))
        for v in self.genes:
            if v.key == key:
                v.set_range(value)
                return

    def provide(self, key: str | tuple[str, ...]) -> GeneDescriptor | None:
        if isinstance(key, str):
            key = tuple(key.split('.'))
        for v in self.genes:
            if v.key == key:
                return v
        return None

    def rnd(self, rnd: random.Random | None = None) -> list[int | float]:
        gene = [0] * len(self.genes)
        to_null = set()
        for g in self.genes:
            value = g.rnd(rnd)
            if g.is_null(value) and g.is_only_nullable_for_filter:
                to_null.add(g.key[:-2])
            gene[g.position] = value
        if len(to_null) > 0:
            for g in self.genes:
                for v in to_null:
                    if g.is_child_of(v):
                        gene = g.set_null(gene)

        return gene

    def gene_space(self) -> list[GeneRange]:
        return [x.get_ranges_secure() for x in self.genes]

    def _clean_nullable_paths(self, kwargs: GeneKwargs) -> GeneKwargs:
        if self.nullable_paths is None:
            return kwargs

        def delete_path(targ: dict[str, dict[str, typing.Any]], path: tuple[str, ...]) -> dict[str, dict[str, typing.Any]] | None:
            curr = path[0]
            if len(path) == 1:
                del targ[curr]
            else:
                targ[curr] = delete_path(targ[curr], path[1:])
                if len(targ[curr]) == 0:
                    del targ[curr]
            return targ

        def is_null_on_path(targ: dict[str, dict[str, typing.Any]], path: tuple[str, ...]) -> bool:
            curr = path[0]
            if curr not in targ:
                return False
            if len(path) == 1:
                return targ[curr] is None
            else:
                return is_null_on_path(targ[curr], path[1:])

        for p in self.nullable_paths:
            if any( is_null_on_path(kwargs, y.key) for y in filter(lambda x: x.is_child_of(p) and x.is_only_nullable_for_filter, self.genes) ):
                kwargs = delete_path(kwargs, p)
        return kwargs

    def gene_to_args(self, gene: Gene) -> GeneKwargs:
        t = {}
        for g in self.genes:
            t = g.set_value_from_gene(gene, t)
        t = self._clean_nullable_paths(t)
        return GeneKwargs(**t)


    def args_to_gene(self, args: GeneKwargs) -> Gene:
        gene = [0] * len(self.genes)
        for g in self.genes:
            gene[g.position] = g.get_gene_value(args)
        return gene

    def gene_is_healthy(self, gene: Gene) -> (bool, list[bool]):
        assert len(gene) == len(self.genes), "Some genes are missing!"
        health_values = [None] * len(self.genes)
        for g in self.genes:
            health_values[g.position] = g.gene_is_valid(gene)
        return all(health_values), health_values

    def gene_type(self) -> list[type]:
        return [value.base_type() for value in self.genes]

    def set_values(self, key: str | tuple[str, ...], values: list[typing.Any], is_optional: bool | None = None):
        if isinstance(key, str):
            key = tuple(key.split('.'))
        for v in self.genes:
            if v.key == key:
                v.set_values(values, is_optional)
                return

    def __len__(self) -> int:
        return len(self.genes)

    def get_paths(self) -> list[tuple[str, ...]]:
        return [x.key for x in self.genes]



_gene_kwargs_map = GeneManager(
    GeneKwargs,
    kwargs = [
        HorizontalKwargs,
        VerticalKwargs,
        NGramBoostKwargs,
        NGramLanguageBoostKwargs,
    ],
    enums = [
        MeanMethod,
        BoostMethod,
        ScoreModifierCalculator,
        BoostNorm,
        FDivergence,
        NormalizeMode,
        Idf,
    ],
    sort=True
)

gene_manager = _gene_kwargs_map


def reset():
    global gene_manager
    gene_manager = _gene_kwargs_map

if __name__ == '__main__':
    gene_manager.set_values("horizontal.divergence", [FDivergence.JensenShannon, FDivergence.NeymanChiSquare, FDivergence.Total])
    gene_manager.set_range("horizontal.factor", [0.5, 0.75, 1.0, 1.5])
    print(gene_manager)

    gene = gene_manager.rnd()
    print(gene)

    kwargs = gene_manager.gene_to_args(gene)
    pprint(kwargs)

    gene2 = gene_manager.args_to_gene(kwargs)
    print(gene2)

    gene2 = gene_manager.args_to_gene(GeneKwargs(
        horizontal=None,
        vertical=None,
        ngram=None,
    ))
    print(gene2)
    print(gene_manager.gene_is_healthy(gene2))
    print(gene_manager.gene_to_args(gene2))

    #
    # print(gene_manager.gene_is_healthy(gene))
    # print(gene_manager.gene_is_healthy(gene2))
    # pprint(gene_manager.gene_space())

