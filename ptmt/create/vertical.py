import typing
from typing import Optional, Protocol

from ldatranslate import BoostNorm, Domain, Register, PyVerticalBoostConfig, FDivergence, ScoreModifierCalculator

from ptmt.create.basic import BasicBoostFactory

class VerticalBoostFactory(Protocol):
    def __call__(self, targets: Optional[list[Domain | Register | int]] = None) -> PyVerticalBoostConfig:
        ...


class VerticalKwargs(typing.TypedDict):
    divergence: FDivergence
    alpha: typing.NotRequired[float]
    score_mod: typing.NotRequired[ScoreModifierCalculator]
    norm: typing.NotRequired[BoostNorm]
    factor: typing.NotRequired[float]
    only_positive_boost: typing.NotRequired[bool]


def create_vertical_factory(
        basic_boost: BasicBoostFactory,
        norm: Optional[BoostNorm] = None,
        factor: Optional[float] = None,
        only_positive_boost: bool | None = None,
        **_rest
) -> VerticalBoostFactory:
    def create(targets: Optional[list[Domain | Register | int]] = None) -> PyVerticalBoostConfig:
        return PyVerticalBoostConfig(
            basic_boost(targets),
            norm,
            factor,
            only_positive_boost
        )
    return create