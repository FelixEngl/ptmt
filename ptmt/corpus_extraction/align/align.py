import re

from . import Article
from .aligned_articles import AlignedArticles
from ..categories import CategorySupplier
from ..parallel_wiki.parsed_article import ParsedArticlePair, ParsedBody, ParsedTitle


def align(parsed: ParsedArticlePair, category_supplier: CategorySupplier) -> AlignedArticles:
    articles = []
    collected = []
    for y in parsed.articles:
        collected_single = []
        for z in y.content:
            if isinstance(z, ParsedBody):
                collected_single.append(z.value)
            if isinstance(z, ParsedTitle):
                a = ''.join(collected_single)
                if len(a) != 0:
                    collected.append(a)
                collected_single.clear()
        if len(collected_single) > 0:
            a = ''.join(collected_single)
            if len(a) != 0:
                collected.append(a)
            collected_single.clear()
        values = re.sub(r'\s+', ' ', ''.join(x for x in collected if len(x.strip()) > 0)).strip()
        articles.append(
            Article(
                y.lang,
                category_supplier.translate_categories(y.lang, y.categories),
                values if len(values) != 0 else None,
                y.is_list
            )
        )
        collected.clear()

    return AlignedArticles(parsed.article_id, *articles)
