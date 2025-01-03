from typing import Protocol, Optional

from ldatranslate import Domain, Register, PyBasicBoostConfig, FDivergence, ScoreModifierCalculator



class BasicBoostFactory(Protocol):
    def __call__(self, targets: Optional[list[Domain | Register | int]] = None) -> PyBasicBoostConfig:
        ...


def create_basic_boost_factory(
    divergence: FDivergence,
    alpha: None | float = None,
    score_mod: ScoreModifierCalculator | None = None,
    **_rest
) -> BasicBoostFactory:
    def create(targets: Optional[list[Domain | Register | int]] = None) -> PyBasicBoostConfig:
        return PyBasicBoostConfig(
            divergence,
            alpha,
            targets,
            False,
            score_mod or ScoreModifierCalculator.WeightedSum
        )
    return create