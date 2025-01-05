from ldatranslate import *

from ptmt.toolkit.combination_creator import *

h_configs_base = dict(
    divergence=FDivergence,
    alpha=Single(1.0),
    score_mod=ScoreModifierCalculator,
    mean=Single(MeanMethod.GeometricMean),
    h_alpha=Alternative(Single(0.5)),
    booster=Single(BoostMethod.Linear),
    linear_transformed=Single(False),
    factor=Alternative(Single(0.5)),
    only_positive_boost=Single(True),
    normalize_mode=Single(NormalizeMode.Sum),
)

v_configs_base = dict(
    # divergence=(FDivergence.Hellinger, FDivergence.KL),
    # alpha=None,
    # score_mod=ScoreModifierCalculator,
    # norm=Single(BoostNorm.Linear),
    # factor=Alternative(Single(0.5)),
    # only_positive_boost=bool,
)

n_config_base = dict(
    # idf=Idf,
    # boosting=Single(BoostMethod.Linear),
    # norm=Single(BoostNorm.Linear),
    # factor=Alternative(Single(0.5)),
    # only_positive_boost=bool,
    # fallback_language=None
)