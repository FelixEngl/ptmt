from collections.abc import Iterable
from typing import Optional, Tuple, List, Union, Iterator
from itertools import chain

from ptmt.dictionary_readers.v1.readers.transformer import BaseTokenClass, ClassedTuple
from ptmt.dictionary_readers.v1.readers.transformer import MetaInfo, AdditionalInfo

LineTreeNodeValue = Union[str, BaseTokenClass, ClassedTuple]


class LineTreeNode(Iterable[LineTreeNodeValue | 'LineTreeNode']):

    _id = 0

    def __init__(self, value: Optional[LineTreeNodeValue] = None, children: Optional[List['LineTreeNode']] = None):
        self.value: Optional[LineTreeNodeValue] = value
        if children is None:
            children = []
        self.children: List[LineTreeNode] = children
        self.parents: List[LineTreeNode] = []
        self.id = LineTreeNode._id
        LineTreeNode._id += 1

    def _add_child(self, child: 'LineTreeNode'):
        self.children.append(child)
        child.parents.append(self)

    def add_child(self,
                  value: Optional[LineTreeNodeValue] = None,
                  *,
                  children: Optional[List['LineTreeNode']] = None) -> 'LineTreeNode':
        child = LineTreeNode(value, children)
        self._add_child(child)
        return child

    def add_branch(self, value: Union[None, BaseTokenClass, 'LineTreeNode']):
        if value is None or isinstance(value, str) or issubclass(type(value), BaseTokenClass):
            branch = LineTreeNode(value)
            branch.children = self.children
        else:
            branch = value
            for leaf in value.get_leafes():
                leaf.children = self.children

        branch.parents = self.parents
        for parent in self.parents:
            parent.children.append(branch)

    def get_leafes(self) -> List['LineTreeNode']:
        stack = [self]
        result = []
        while len(stack) != 0:
            act = stack.pop(0)
            if act.is_leaf:
                result.append(act)
            else:
                stack = stack+act.children
        return result

    def __repr__(self):
        match self.value:
            case None:
                return "LTN()"
            case str():
                return f"LTN('{self.value}')"
            case BaseTokenClass():
                return f"LTN({repr(self.value)})"
            case _:
                raise TypeError("Unsupported Type")

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    @property
    def is_filler(self) -> bool:
        return self.value is None

    @property
    def is_text(self) -> bool:
        return isinstance(self.value, str)

    @property
    def is_meta(self) -> bool:
        # assert isinstance(self.value, MetaInfo) == (type(self.value).__name__ == "MetaInfo")
        return isinstance(self.value, MetaInfo)

    @property
    def is_add(self) -> bool:
        # assert isinstance(self.value, AdditionalInfo) == (type(self.value).__name__ == "AdditionalInfo")
        return isinstance(self.value, AdditionalInfo)

    def get_all_combinations(self,
                             before: Optional[Tuple['LineTreeNode', ...]] = None) -> \
            Iterator[Tuple['LineTreeNode', ...]]:
        if before is None:
            if self.is_filler:
                state = None
            else:
                state = (self, )
        else:
            if self.is_filler:
                state = before
            else:
                state = before + (self, )
        if self.is_leaf:
            yield state
        else:
            for ch in self.children:
                yield from ch.get_all_combinations(state)

    def __str__(self):
        if isinstance(self.value, str):
            return str(self.value)
        else:
            return ','.join(map(str, chain.from_iterable(self.value.value))).replace("/", "").replace("-", ",")

    def __iter__(self) -> Iterator[LineTreeNodeValue | 'LineTreeNode']:
        if self.value is not None:
            yield self.value
        yield from self.children

    def deep_iter(self) -> Iterator[LineTreeNodeValue]:
        for x in iter(self):
            match x:
                case LineTreeNode():
                    yield from x
                case _:
                    yield x


class MetaTuple(tuple[str, ...]):
    pass


class LineTree:
    def __init__(self):
        self.root: LineTreeNode = LineTreeNode()
