import nltk
from nltk.corpus import stopwords


def get_stop_words(lang: str) -> set[str]:
    try:
        return set(stopwords.words(lang))
    except LookupError:
        nltk.download('stopwords')
        return set(stopwords.words(lang))
