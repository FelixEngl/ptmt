import typing
from typing import Protocol, Optional

from ldatranslate import Domain, Register, PyHorizontalBoostConfig, MeanMethod, BoostMethod, FDivergence, \
    ScoreModifierCalculator, NormalizeMode

from ptmt.create.basic import BasicBoostFactory


class HorizontalBoostFactory(Protocol):
    def __call__(self, targets: Optional[list[Domain | Register | int]] = None) -> PyHorizontalBoostConfig:
        ...



class HorizontalKwargs(typing.TypedDict):
    divergence: FDivergence
    alpha: typing.NotRequired[float]
    score_mod: typing.NotRequired[ScoreModifierCalculator]
    mean: typing.NotRequired[MeanMethod]
    h_alpha: typing.NotRequired[float]
    booster: typing.NotRequired[BoostMethod]
    linear_transformed: typing.NotRequired[bool]
    factor: typing.NotRequired[float]
    only_positive_boost: typing.NotRequired[bool]
    normalize_mode: typing.NotRequired[NormalizeMode]

def create_horizontal_factory(
        basic_boost: BasicBoostFactory,
        mean: Optional[MeanMethod] = None,
        h_alpha: Optional[float] = None,
        linear_transformed: Optional[bool] = None,
        booster: Optional[BoostMethod] = None,
        factor: Optional[float] = None,
        only_positive_boost: Optional[float] = None,
        normalize_mode: Optional[NormalizeMode] = None,
        **_rest
) -> HorizontalBoostFactory:
    def create(targets: Optional[list[Domain | Register | int]] = None) -> PyHorizontalBoostConfig:
        return PyHorizontalBoostConfig(
            basic_boost(targets),
            mean,
            alpha=h_alpha,
            linear_transformed=linear_transformed,
            booster=booster,
            factor=factor,
            only_positive_boost=only_positive_boost,
            normalize_mode=normalize_mode
        )

    return create
