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
