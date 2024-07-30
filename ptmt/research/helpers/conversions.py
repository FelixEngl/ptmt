from ldatranslate.ldatranslate import PyArticle, PyAlignedArticle

from ptmt.corpus_extraction.align import Article, AlignedArticles


def convert_article(article: PyArticle) -> Article:
    return Article(
        str(article.lang),
        article.categories,
        article.content,
        article.is_list
    )


def convert_aligned_article(aligned_article: PyAlignedArticle) -> AlignedArticles:
    return AlignedArticles(
        aligned_article.article_id,
        *tuple(convert_article(aligned_article[value]) for value in aligned_article.language_hints)
    )
