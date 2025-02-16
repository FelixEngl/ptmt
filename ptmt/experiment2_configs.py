from ldatranslate import *

from ptmt.toolkit.combination_creator import *

# v3_V#_HdJSa1-0000sMmMMGMh0-5000bLlFf0-5000oTnS_N#
# v3_V#_HdNCSa1-0000sMmMMGMh0-5000bLlFf0-5000oTnS_N#
# v3_V#_HdTa1-0000sMmMMGMh0-5000bLlFf0-5000oTnS_N#
# v3_V#_HdTa1-0000sWSmMMGMh0-5000bLlFf0-5000oTnS_N#

h_configs_base = dict(
    divergence=[FDivergence.JensenShannon, FDivergence.NeymanChiSquare, FDivergence.Total], # B weniger gut, CA+JS vielversprechend
    alpha=Single(1.0),
    score_mod=ScoreModifierCalculator,
    mean=MeanMethod,
    h_alpha=Alternative(Single(0.5)),
    booster=BoostMethod,
    linear_transformed=bool,
    factor=Alternative([0.5, 0.75, 1.0, 1.5]),
    only_positive_boost=bool,
    normalize_mode=NormalizeMode,
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