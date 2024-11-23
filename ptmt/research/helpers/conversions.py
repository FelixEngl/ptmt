# Copyright 2024 Felix Engl
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ldatranslate import PyArticle, PyAlignedArticle

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
