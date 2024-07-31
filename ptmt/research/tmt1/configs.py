import dataclasses
import typing

from ldatranslate.ldatranslate import PyTranslationConfig, KeepOriginalWord

from ptmt.research.protocols import TranslationConfig

VotingConfig = typing.NamedTuple('VotingConfig', [
    ('name_shown', str),
    ('voting_name', str),
    ('voting', str),
    ('limit', int | None),
    ('is_baseline', bool)
])


votings = [
   VotingConfig(r"\text{Plain}", "original", "OriginalScore", None, True),
   VotingConfig(r"\text{Plain}", "original", "OriginalScore", 2, True),
   VotingConfig(r"\text{Plain}", "original", "OriginalScore", 3, True),
   VotingConfig(r"\text{CombSUM}", "combSum", "CombSum", None, False),
   VotingConfig(r"\text{CombSUM}", "combSum", "CombSum", 2, False),
   VotingConfig(r"\text{CombSUM}", "combSum", "CombSum", 3, False),
   VotingConfig(r"\text{CombSUM}\;\text{RR}^2", "combSumRr2", "CombSumRRPow2", None, False),
   VotingConfig(r"\text{CombSUM}\;\text{RR}^2", "combSumRr2", "CombSumRRPow2", 2, False),
   VotingConfig(r"\text{CombSUM}\;\text{RR}^2", "combSumRr2", "CombSumRRPow2", 3, False),
   VotingConfig(r"\text{RR}", "rr", "RR", None, False),
   VotingConfig(r"\text{RR}", "rr", "RR", 2, False),
   VotingConfig(r"\text{RR}", "rr", "RR", 3, False),
   VotingConfig(r"\text{CombGSUM}", "gCombSum", "GCombSum", None, False),
   VotingConfig(r"\text{CombGSUM}", "gCombSum", "GCombSum", 2, False),
   VotingConfig(r"\text{CombGSUM}", "gCombSum", "GCombSum", 3, False),
   VotingConfig(r"\text{CombNOR}", "combNor", "WCombSum", None, False),
   VotingConfig(r"\text{CombNOR}", "combNor", "WCombSum", 2, False),
   VotingConfig(r"\text{CombNOR}", "combNor", "WCombSum", 3, False),
   VotingConfig(r"\text{CombGNOR}", "combGNor", "WGCombSum", None, False),
   VotingConfig(r"\text{CombGNOR}", "combGNor", "WGCombSum", 2, False),
   VotingConfig(r"\text{CombGNOR}", "combGNor", "WGCombSum", 3, False),
   VotingConfig(r"\text{CombRR PEN}", "combRrPen", "PCombSum", None, False),
   VotingConfig(r"\text{CombRR PEN}", "combRrPen", "PCombSum", 2, False),
   VotingConfig(r"\text{CombRR PEN}", "combRrPen", "PCombSum", 3, False),
]

BasicTranslationConfig = typing.NamedTuple('BasicTranslationConfig', [
    ('special_dict', bool),
    ('keep_original', KeepOriginalWord)
])

secondary_configs = [
    BasicTranslationConfig(True, KeepOriginalWord.Always),
    BasicTranslationConfig(True, KeepOriginalWord.Never),
    BasicTranslationConfig(True, KeepOriginalWord.IfNoTranslation),
    BasicTranslationConfig(False, KeepOriginalWord.Always),
    BasicTranslationConfig(False, KeepOriginalWord.Never),
    BasicTranslationConfig(False, KeepOriginalWord.IfNoTranslation)
]


@dataclasses.dataclass(repr=True)
class TranslationConfigV1(TranslationConfig):
    name_in_table: str
    config_id: str
    config_ids: tuple[int, int]
    voting: str
    limited_dictionary: bool
    keep: KeepOriginalWord
    limit: None | int
    is_baseline: bool
    alpha: None | float | list[float] = dataclasses.field(default=None)

    def to_translation_config(self) -> PyTranslationConfig:
        return PyTranslationConfig(
            None,
            None,
            self.keep,
            None,
        )

    def __getstate__(self) -> dict[str, typing.Any]:
        current = self.__dict__.copy()
        current["keep"] = str(self.keep)
        return current

    def __setstate__(self, state: dict[str, typing.Any]):
        state["keep"] = KeepOriginalWord.from_string(state.pop("keep"))
        self.__dict__.update(state)

    def raw_voting_config(self) -> VotingConfig | None:
        return votings[self.config_ids[0]]

    def raw_secondary_config(self) -> BasicTranslationConfig | None:
        return secondary_configs[self.config_ids[1]]


def construct_real_voting_and_name(voting_config: tuple[str, str, str, int | None, bool]) -> tuple[str, str]:
    """real_voting, real_name_shown"""
    name_shown, voting_name, voting, limit, _ = voting_config
    if limit is not None:
        real_voting = voting + "(" + str(limit) + ")"
        real_name_shown = name_shown + r'\;\text{TOP}_{' + str(limit) + '}'
    else:
        real_voting = voting
        real_name_shown = name_shown
    real_name_shown = f"${real_name_shown}$"
    return real_voting, real_name_shown


def create_configs() -> list[TranslationConfig]:

    configs = []

    for idx1, t in enumerate(votings):
        voting_id = chr(ord('A') + idx1)
        name_shown, voting_name, voting, limit, is_baseline = t
        for idx2, special_voc_and_keep in enumerate(secondary_configs):
            special, keep = special_voc_and_keep
            real_voting, real_name_shown = construct_real_voting_and_name(t)
            real_id = voting_id + str(idx2)
            configs.append(
                TranslationConfigV1(
                    real_name_shown,
                    real_id,
                    (idx1, idx2),
                    real_voting,
                    special,
                    keep,
                    limit,
                    is_baseline
                )
            )


    return configs
