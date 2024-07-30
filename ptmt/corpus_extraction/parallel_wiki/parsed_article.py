import dataclasses
from .raw_article import RawArticlePair, RawContent, RawHeader, RawBody


@dataclasses.dataclass(slots=True)
class ParsedTitle:
    value: str


@dataclasses.dataclass(slots=True)
class ParsedBody:
    value: str


ParsedContent = ParsedTitle | ParsedBody


@dataclasses.dataclass(slots=True)
class ParsedArticle:
    lang: str
    title: str
    categories: tuple[str] | None
    content: tuple[ParsedContent, ...]
    is_list: bool


@dataclasses.dataclass(slots=True)
class ParsedArticlePair:
    article_id: int
    articles: tuple[ParsedArticle, ...]


def _clean(cont: str | None) -> str:
    match cont:
        case None | '\n':
            return ''
        case str():
            return cont.replace('\n', ' ')


def _str(cont: RawContent) -> str:
    return _clean(cont.text) + _clean(cont.tail)


def _to_parsed(unparsed_type: RawContent, content: list[str]) -> ParsedContent:
    con = ' '.join(content)
    if unparsed_type is RawBody:
        return ParsedBody(con)
    elif unparsed_type is RawHeader:
        return ParsedTitle(con)
    else:
        raise ValueError(f"{unparsed_type}")


def parse(article_pair: RawArticlePair) -> ParsedArticlePair:
    articles = []
    for article in article_pair.articles:
        last_type = None
        content = []
        single_content = []
        skip_until_next_header = False
        for content_element in article.content:
            s = _str(content_element)
            tmp = type(content_element)
            if isinstance(content_element, RawHeader):
                if content_element.text in ('Einzelnachweise', 'References', 'Belege', 'Literatur'):
                    skip_until_next_header = True
                    continue
                elif skip_until_next_header:
                    skip_until_next_header = False
            elif skip_until_next_header:
                continue
            if last_type is None:
                last_type = tmp
            elif last_type != tmp:
                content.append(_to_parsed(last_type, single_content))
                single_content.clear()
                last_type = tmp
            single_content.append(s)
        content.append(_to_parsed(last_type, single_content))

        articles.append(
            ParsedArticle(
                article.lang,
                article.title,
                tuple(article.categories),
                tuple(content),
                article.is_list
            )
        )
    return ParsedArticlePair(article_pair.article_id, tuple(articles))


