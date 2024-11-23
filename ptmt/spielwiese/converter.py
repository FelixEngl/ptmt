from collections import defaultdict
from typing import TypedDict

POSMap = TypedDict(
    "POSMap",
    {
        "pos": str,
        "debug": str,
        "tags": list[str],
    },
    total=False,
)


part_of_speech_map: dict[str, POSMap] = {
    "abbreviation": {
        "pos": "abbrev",
        "debug": "part-of-speech Abbreviation is proscribed",
        "tags": ["abbreviation"],
    },
    "acronym": {
        "pos": "abbrev",
        "debug": "part-of-speech Acronym is proscribed",
        "tags": ["abbreviation"],
    },
    "adjectival": {
        "pos": "adj_noun",
        "debug": "part-of-speech Adjectival is not valid",
    },
    "adjectival noun": {
        # Not listed as allowed, but common
        "pos": "adj_noun",
    },
    "adjectival verb": {
        # Not listed as allowed, but common
        "pos": "adj_verb",
    },
    "adjective": {
        "pos": "adj",
    },
    "adjectuve": {
        "pos": "adj",
        "debug": "misspelled subtitle",
    },
    "adjectives": {
        "pos": "adj",
        "debug": "usually used in singular",
    },
    "adnominal": {
        "pos": "adnominal",
    },
    "adverb": {
        "pos": "adv",
    },
    "adverbs": {
        "pos": "adv",
        "debug": "usually used in singular",
    },
    "adverbial phrase": {
        "pos": "adv_phrase",
        "debug": "part-of-speech Adverbial phrase is proscribed",
    },
    "affix": {
        "pos": "affix",
    },
    "adjective suffix": {
        "pos": "suffix",
        "debug": "part-of-speech Adjective suffix is proscribed",
    },
    "ambiposition": {
        "pos": "ambiposition",
    },
    "article": {
        "pos": "article",
    },
    "character": {
        "pos": "character",
    },
    "circumfix": {
        "pos": "circumfix",
        "tags": ["morpheme"],
    },
    "circumposition": {
        "pos": "circumpos",
    },
    "classifier": {
        "pos": "classifier",
    },
    "clipping": {
        "pos": "abbrev",
        "debug": "part-of-speech Clipping is proscribed",
        "tags": ["abbreviation"],
    },
    "clitic": {
        "pos": "suffix",
        "debug": "part-of-speech Clitic is proscribed",
        "tags": ["clitic"],
    },
    "combining form": {
        "pos": "combining_form",
        "tags": ["morpheme"],
    },
    "comparative": {
        "pos": "adj",
        "tags": ["comparative"],
    },
    "conjunction": {
        "pos": "conj",
    },
    "conjuntion": {
        "pos": "conj",
        "debug": "misspelled subtitle",
    },
    "contraction": {
        "pos": "contraction",
        "tags": ["abbreviation"],
    },
    "converb": {
        "pos": "converb",
    },
    "counter": {
        "pos": "counter",
    },
    "dependent noun": {
        "pos": "noun",
        "tags": [
            "dependent",
        ],
    },
    "definitions": {
        # This is used under chinese characters
        "pos": "character",
    },
    "determiner": {
        "pos": "det",
    },
    "diacritical mark": {
        "pos": "character",
        "tags": ["diacritic"],
    },
    "enclitic": {
        "pos": "suffix",
        "tags": ["clitic"],
    },
    "enclitic particle": {
        "pos": "suffix",
        "tags": ["clitic"],
    },
    "gerund": {
        "pos": "verb",
        "debug": "part-of-speech Gerund is proscribed",
        "tags": ["participle", "gerund"],
    },
    "han character": {
        "pos": "character",
        "tags": ["han"],
    },
    "han characters": {
        "pos": "character",
        "tags": ["han"],
        "debug": "psually used in singular",
    },
    "hanja": {
        "pos": "character",
        "tags": ["Hanja"],
    },
    "hanzi": {
        "pos": "character",
        "tags": ["hanzi"],
    },
    "ideophone": {
        "pos": "noun",
        "tags": ["ideophone"],
    },
    "idiom": {
        "pos": "phrase",
        "tags": ["idiomatic"],
        # This is too common for now to complain about
        # "debug": "part-of-speech Idiom is proscribed",
    },
    "infix": {
        "pos": "infix",
        "tags": ["morpheme"],
    },
    "infinitive": {
        "pos": "verb",
        "debug": "part-of-speech Infinitive is proscribed",
        "tags": ["infinitive"],
    },
    "initialism": {
        "pos": "abbrev",
        "debug": "part-of-speech Initialism is proscribed",
        "tags": ["abbreviation"],
    },
    "interfix": {
        "pos": "interfix",
        "tags": ["morpheme"],
    },
    "interjection": {
        "pos": "intj",
    },
    "interrogative pronoun": {
        "pos": "pron",
        "tags": ["interrogative"],
    },
    "intransitive verb": {
        "pos": "verb",
        "debug": "part-of-speech Intransitive verb is proscribed",
        "tags": ["intransitive"],
    },
    "instransitive verb": {
        "pos": "verb",
        "tags": ["intransitive"],
        "debug": "pisspelled subtitle",
    },
    "kanji": {
        "pos": "character",
        "tags": ["kanji"],
    },
    "letter": {
        "pos": "character",
        "tags": ["letter"],
    },
    "ligature": {
        "pos": "character",
        "tags": ["ligature"],
    },
    "nominal nuclear clause": {
        "pos": "clause",
        "debug": "part-of-speech Nominal nuclear clause is proscribed",
    },
    "νoun": {
        "pos": "noun",
        "debug": "misspelled subtitle",
    },
    "nouɲ": {
        "pos": "noun",
        "debug": "misspelled subtitle",
    },
    "noun": {
        "pos": "noun",
    },
    "noun form": {
        "pos": "noun",
        "debug": "part-of-speech Noun form is proscribed",
    },
    "nouns": {
        "pos": "noun",
        "debug": "usually in singular",
    },
    "noum": {
        "pos": "noun",
        "debug": "misspelled subtitle",
    },
    "number": {
        "pos": "num",
        "tags": ["number"],
    },
    "numeral": {
        "pos": "num",
    },
    "ordinal number": {
        "pos": "adj",
        "debug": "ordinal numbers should be adjectives",
        "tags": ["ordinal"],
    },
    "participle": {
        "pos": "verb",
        "tags": ["participle"],
    },
    "particle": {
        "pos": "particle",
        # XXX Many of these seem to be prefixes or suffixes
    },
    "past participle": {
        "pos": "verb",
        "tags": ["participle", "past"],
    },
    "perfect expression": {
        "pos": "verb",
    },
    "perfection expression": {
        "pos": "verb",
    },
    "perfect participle": {
        "pos": "verb",
        "tags": ["participle", "perfect"],
    },
    "personal pronoun": {
        "pos": "pron",
        "tags": ["person"],
    },
    "phrase": {
        "pos": "phrase",
    },
    "phrases": {
        "pos": "phrase",
        "debug": "usually used in singular",
    },
    "possessive determiner": {
        "pos": "det",
        "tags": ["possessive"],
    },
    "possessive pronoun": {
        "pos": "det",
        "tags": ["possessive"],
    },
    "postposition": {
        "pos": "postp",
    },
    "predicative": {
        "pos": "adj",
        "tags": ["predicative"],
    },
    "prefix": {
        "pos": "prefix",
        "tags": ["morpheme"],
    },
    "preposition": {
        "pos": "prep",
    },
    "prepositions": {
        "pos": "prep",
        "debug": "usually used in singular",
    },
    "prepositional expressions": {
        "pos": "prep",
        "debug": "part-of-speech Prepositional expressions is proscribed",
    },
    "prepositional phrase": {
        "pos": "prep_phrase",
    },
    "prepositional pronoun": {
        "pos": "pron",
        "debug": "part-of-speech Prepositional pronoun is proscribed",
        "tags": ["prepositional"],
    },
    "present participle": {
        "pos": "verb",
        "debug": "part-of-speech Present participle is proscribed",
        "tags": ["participle", "present"],
    },
    "preverb": {
        "pos": "preverb",
    },
    "pronoun": {
        "pos": "pron",
    },
    "proper noun": {
        "pos": "name",
    },
    "proper oun": {
        "pos": "name",
        "debug": "misspelled subtitle",
    },
    "proposition": {
        "pos": "prep",  # Appears to be a misspelling of preposition
        "debug": "misspelled subtitle",
    },
    "proverb": {
        "pos": "proverb",
    },
    "punctuation mark": {
        "pos": "punct",
        "tags": ["punctuation"],
    },
    "punctuation": {
        "pos": "punct",
        "debug": "part-of-speech Punctuation should be Punctuation mark",
        "tags": ["punctuation"],
    },
    "relative": {
        "pos": "conj",
        "tags": ["relative"],
    },
    "romanization": {
        "pos": "romanization",
    },
    "root": {
        "pos": "root",
        "tags": ["morpheme"],
    },
    "suffix": {
        "pos": "suffix",
        "tags": ["morpheme"],
    },
    "suffix form": {
        "pos": "suffix",
        "debug": "part-of-speech Suffix form is proscribed",
        "tags": ["morpheme"],
    },
    "syllable": {
        "pos": "syllable",
    },
    "symbol": {
        "pos": "symbol",
    },
    "transitive verb": {
        "pos": "verb",
        "tags": ["transitive"],
    },
    "verb": {
        "pos": "verb",
    },
    "verb form": {
        "pos": "verb",
        "debug": "part-of-speech Verb form is proscribed",
    },
    "verbal noun": {
        "pos": "noun",
        "tags": ["verbal"],
    },
    "verbs": {
        "pos": "verb",
        "debug": "usually in singular",
    },
    "adj": {
        "pos": "adj",
    },
    "adv": {
        "pos": "adv"
    },
    "adv.": {
        "pos": "adv"
    },
    "v": {
        "pos": "verb"
    },
    "conj": {
        "pos": "conj"
    },
    "ppron": {
        "pos": "pron"
    },
    "pron": {
        "pos": "pron"
    },
    "prp": {
        "pos": "prep"
    },
    "prep": {
        "pos": "prep"
    },
    "det": {
        "pos": "det"
    },
    "int": {
        "pos": "intj"
    },
    "interj": {
        "pos": "intj"
    },
    "pres-p": {
        "pos": "verb",
        "tags": ["participle", "present"],
    },
    "past-p": {
        "pos": "verb",
        "tags": ["participle", "past"],
    },
    "art": {
        "pos": "article",
    },
    "ptcl": {
        "pos": "particle",
    },
    "Partikel": {
        "pos": "particle",
    },
    "pnoun": {
        "pos": "name",
    },
    "misc": {
        "pos": "other",
    },
    "other": {
        "pos": "other",
    },
    "indart": {
        "pos": "article",
        "tags": ["indefinite"],
    },
    "indefinite article": {
        "pos": "article",
        "tags": ["indefinite"],
    },
    "pron interrog": {
        "pos": "pron",
        "tags": ["interrogative"],
    },
    "relativ.pron": {
        "pos": "pron",
        "tags": ["relative"],
    },
}


def to_camel_case(snake_str):
    return "".join(x.capitalize() for x in snake_str.lower().split("_"))


def create_pos():
    pos_data = defaultdict(lambda: defaultdict(set))
    for k, v in part_of_speech_map.items():
        dat = pos_data[v["pos"]]
        dat["name"].add(k)
        if 'tags' in v:
            for t in v["tags"]:
                dat["tags"].add(t)

    p_d = defaultdict(lambda: 999999999999999999)
    p_d["noun"] = -10
    p_d["verb"] = -9
    p_d["adv"] = -8
    p_d["pron"] = -5
    p_d["conj"] = -3
    p_d["prep"] = -3
    p_d["num"] = -2
    p_d["det"] = -2
    p_d["intj"] = -2
    p_d["article"] = -1
    p_d["prefix"] = -1
    p_d["suffix"] = -1
    p_d["name"] = -1
    p_d["particle"] = 0
    p_d["character"] = 0
    p_d["other"] = 1
    d = sorted(pos_data.items(), key=lambda x: (p_d[x[0]], x[0]))

    dat_pos = [
        '#[cfg_attr(feature="gen_python_api", pyo3_stub_gen::derive::gen_stub_pyclass_enum)]',
        '#[pyclass(eq, eq_int, hash, frozen)]',
        '#[derive(Copy, Clone, Debug, Eq, PartialEq, Hash, Ord, PartialOrd)]',
        '#[derive(Display, EnumString, IntoStaticStr, EnumIter)]',
        '#[derive(TryFromPrimitive, IntoPrimitive, Serialize, Deserialize)]',
        '#[repr(u64)]',
        "pub enum PartOfSpeech {"
    ]
    for i, u in enumerate(d):
        main_tag, tags_and_names = u
        main_tag: str
        tags_and_names: dict[str, set[str]]

        # pos data
        name = main_tag.capitalize()
        if len(tags_and_names["tags"]) > 0:
            dat_pos.append(f"    /// Associated Tags:")
            dat_pos.append(f"    /// ```plaintext")
            for t in tags_and_names["tags"]:
                dat_pos.append(f"    ///    - {t}")
            dat_pos.append(f"    /// ```")
        dat_pos.append(f'    #[strum(to_string = "{main_tag}", serialize = "{name}")]')
        s = {main_tag, name}
        for n in tags_and_names["name"]:
            old = len(s)
            s.add(n)
            if old == len(s):
                continue
            dat_pos.append(f'    #[strum(serialize = "{n}")]')
        name = to_camel_case(name)
        dat_pos.append(f'    {name} = {i},\n')
    dat_pos.append("}")

    print('\n'.join(dat_pos))


def create_tags():
    tag_data = defaultdict(lambda: defaultdict(set))
    tag_method_data = dict()
    for k, v in part_of_speech_map.items():
        if 'tags' in v:
            for t in v["tags"]:
                dat = tag_data[t]
                dat["targets"].add(k)
                dat["pos"].add(v["pos"])
            assert k not in tag_method_data;
            tag_method_data[k] = v["tags"]

    p_d = defaultdict(lambda: 999999999999999999)
    p_d["transitive"] = -10
    p_d["participle"] = -10
    p_d["present"] = -10
    p_d["past"] = -10
    p_d["morpheme"] = -10
    p_d["det"] = -10

    p_d["ideophone"] = -9
    p_d["verbal"] = -9
    p_d["perfect"] = -9

    p_d["past"] = -8
    p_d["intransitive"] = -8
    p_d["gerund"] = -8
    p_d["infinitive"] = -8
    p_d["interrogative"] = -8
    p_d["person"] = -7
    p_d["prepositional"] = -7
    p_d["relative"] = -7
    d = sorted(tag_data.items(), key=lambda x: (p_d[x[0]], x[0]))

    dat_pos = [
        '#[cfg_attr(feature="gen_python_api", pyo3_stub_gen::derive::gen_stub_pyclass_enum)]',
        '#[pyclass(eq, eq_int, hash, frozen)]',
        '#[derive(Copy, Clone, Debug, Eq, PartialEq, Hash, Ord, PartialOrd)]',
        '#[derive(Display, EnumString, IntoStaticStr, EnumIter)]',
        '#[derive(TryFromPrimitive, IntoPrimitive, Serialize, Deserialize)]',
        '#[repr(u64)]',
        "pub enum PartOfSpeechTags {"
    ]



    for i, u in enumerate(d):
        main_tag, targets_and_pos = u
        main_tag: str
        targets_and_pos: dict[str, set[str]]
        name = main_tag.capitalize()
        dat_pos.append(f"    /// Associated Pos:")
        dat_pos.append(f"    /// ```plaintext")
        for t in targets_and_pos["pos"]:
            dat_pos.append(f"    ///    - {t}")
        dat_pos.append(f"    /// ```")

        dat_pos.append(f"    /// Associated Targets:")
        dat_pos.append(f"    /// ```plaintext")
        for t in targets_and_pos["targets"]:
            dat_pos.append(f"    ///    - {t}")
        dat_pos.append(f"    /// ```")
        main_tag = main_tag.lower()
        dat_pos.append(f'    #[strum(to_string = "{main_tag}", serialize = "{name}")]')
        name = to_camel_case(name)
        dat_pos.append(f'    {name} = {i},\n')

    dat_pos.append("}")

    constants = dict()

    associate_pos = [
        "impl PartOfSpeechTags {",
        "    pub fn get_tags(target: &str) -> Option<&'static [PartOfSpeechTags]> {",
        "        match target {",
    ]

    for target, tags in tag_method_data.items():
        tags = list(tags)
        tags.sort()
        name = "_".join(x.upper() for x in tags)
        entry = (", ".join(f'PartOfSpeechTags::' + x.capitalize() for x in tags), len(tags))
        if name not in constants:
            constants[name] = entry
        else:
             assert constants[name] == entry
        associate_pos.append(f'            "{target}" => Some(&Self::{name}),')
    associate_pos.append("            _ => None")
    associate_pos.append("        }")
    associate_pos.append("    }\n\n")

    for k, v in constants.items():
        associate_pos.append(f"    pub const {k}: [PartOfSpeechTags; {v[1]}] = [{v[0]}];")

    associate_pos.append("}")

    print('\n'.join(dat_pos))
    print('\n'.join(associate_pos))


if __name__ == '__main__':
    create_pos()
    print("\n\n")
    create_tags()








