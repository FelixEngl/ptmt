import collections
import dataclasses
import typing
from typing import Iterator
import re
import lxml.etree as ET


@dataclasses.dataclass(slots=True)
class RawHeader:
    text: str | None
    tail: str | None


@dataclasses.dataclass(slots=True)
class RawBody:
    text: str | None
    tail: str | None


RawContent = RawHeader | RawBody


@dataclasses.dataclass(slots=True)
class RawArticle:
    lang: str
    title: str
    categories: list[str]
    content: list[RawContent]
    is_list: bool


@dataclasses.dataclass(slots=True)
class RawArticlePair:
    article_id: int
    articles: tuple[RawArticle, ...]

    @property
    def is_list(self) -> bool:
        return len(self.articles) != 0 and any(x for x in self.articles if x.is_list)


class IllegalNesting(ValueError):
    pass


class IllegalPosition(ValueError):
    pass


class IllegalNumberOfArticles(ValueError):
    pass


def extract(source: typing.TextIO | typing.BinaryIO) -> Iterator[RawArticlePair]:
    """
    Extracts a raw article pairs from any source that is valid for lxml.etree.iterparse
    """
    articles_id = None
    articles = None

    in_content: bool = False
    current_content: list[RawContent] | None = None
    current_lang: str | None = None
    current_title: str | None = None
    current_categories: list[str] | None = None

    stack = collections.deque()
    art_ct = 0
    for event, element in ET.iterparse(source, encoding='UTF-8', events=('start', 'end'), no_network=True, recover=True):
        element: ET.ElementBase
        if event == "start":
            if element.tag == 'article' and 'article' in stack:
                raise IllegalNesting(f"Article <{element.tag} {element.attrib}> is at an illegal position!")
            stack.append(element.tag)
        else:
            assert event == 'end'
            old = stack.pop()
            if old != element.tag:
                raise IllegalNesting(
                    f"The tag <{element.tag}> does not match the tag on the stack <{old}>!"
                )

        match event, element.tag, in_content:
            case "start", "articlePair", False:
                articles_id = int(element.attrib["id"])
                articles = list()
            case "end", "articlePair", False:
                if art_ct != 2:
                    raise IllegalNumberOfArticles(f"Expected 2 but got {art_ct}")
                art_ct = 0
                yield RawArticlePair(articles_id, tuple(articles))
            case "start", "article", False:
                art_ct += 1
                current_lang = element.attrib["lang"]
                current_title = element.attrib["name"]
            case "start", "categories", False:
                current_categories = list(filter(lambda x: len(x) > 0, element.attrib["name"].split("|")))
            case "end", "categories", False:
                pass
            case "end", "article", False:

                is_list = False
                for cat in current_categories:
                    if re.search("List[se]", cat) is not None:
                        is_list = True

                articles.append(
                    RawArticle(
                        current_lang,
                        current_title,
                        current_categories,
                        current_content,
                        is_list
                    )
                )
                current_content = None
                current_categories = None
                current_lang = None
                current_title = None
            case "start", "content", False:
                in_content = True
                current_content = []
            case "end", "content", True:
                in_content = False
            case "end", "h", True:
                bod = RawHeader(element.text, None)
                current_content.append(bod)
                current_content.append(RawBody(None, element.tail))
            case "end", "table", True:
                current_content.append(RawBody(None, element.tail))
            case "start", "p", True:
                current_content.append(RawBody(element.text, element.tail))
            case "end", "p" | "link" | "math", True:
                bod = RawBody(element.text, element.tail)
                last = current_content[-1]
                if last.tail == bod.text:
                    bod = dataclasses.replace(bod, text=None)
                if bod in current_content:
                    continue
                current_content.append(bod)
            case "start", "link" | "math" | "table" | "h" | "cell", True:
                pass
            case i, "link" | "math" | "table" | "h" | "cell" | "p", False:
                raise IllegalPosition(f"{element.tag} at {i} is not supposed to be outside of content!")
            case "start", unkn, in_content:
                print(f"Start unknown({in_content}): {unkn}")
            case _, "wikipediaSource" | "header" | "cell", _:
                pass
            case _, missed, _:
                print(f"Missed: {missed}")
