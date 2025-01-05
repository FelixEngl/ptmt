from ldatranslate import FDivergence, ScoreModifierCalculator, MeanMethod, BoostMethod, NormalizeMode, BoostNorm, Idf

from ptmt.toolkit.combination_creator import Alternative

full_h = dict(
    divergence=FDivergence,
    alpha=Alternative((0.5, 1.5, 3)),
    score_mod=ScoreModifierCalculator,
    mean=MeanMethod,
    h_alpha=Alternative((0.5, 1.5, 3)),
    booster=BoostMethod,
    linear_transformed=bool,
    factor=Alternative((0.5, 1.5, 3)),
    only_positive_boost=bool,
    normalize_mode=NormalizeMode,
)

full_v = dict(
    divergence=FDivergence,
    alpha=Alternative((0.5, 1.5, 3)),
    score_mod=ScoreModifierCalculator,
    norm=BoostNorm,
    factor=Alternative((0.5, 1.5, 3)),
    only_positive_boost=bool,
)

full_n = dict(
    idf=Idf,
    boosting=BoostMethod,
    norm=BoostNorm,
    factor=Alternative((0.5, 1.5, 3)),
    only_positive_boost=bool,
    fallback_language=None
)