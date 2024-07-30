import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterator, Optional
from lxml import etree
import lxml.etree as ET
from lxml.etree import _Element as Element
from mwparserfromhell.wikicode import Wikicode
from ptmt.toolkit.paths import str_to_path, PathObj
import mwparserfromhell


@dataclass
class WiktionaryData:
    id: int
    title: str
    text: str


# {http://www.mediawiki.org/xml/export-0.10/}
@str_to_path
def read_wiktionary(file: PathObj) -> Iterator[WiktionaryData]:
    for event, element in ET.iterparse(str(file.absolute()), tag=['{*}page'], encoding='UTF-8'):
        element: Element
        title: Optional[Element] = element.find('{*}title')
        text: Optional[Element] = element.find('{*}revision/{*}text')
        _id: Optional[Element] = element.find('{*}id')
        if title is not None and text is not None:
            yield WiktionaryData(int(_id.text), title.text, text.text)
        if etree.QName(element).localname == "page":
            element.clear()


_is_meta_page = re.compile(r"(MediaWiki|Wiktionary|User|User\stalk|Wiktionary\sDiskussion|Verzeichnis|Diskussion|Wiktionary\stalk):.*")


def apply_filter(it: Iterator[WiktionaryData]) -> Iterator[WiktionaryData]:
    return filter(lambda x: not _is_meta_page.match(x.title), it)


class NoTranslationEntryException(Exception):
    def __init__(self, entry: WiktionaryData):
        self.entry: WiktionaryData = entry

    def __str__(self):
        return f'The title "{self.entry.title}" does not contain a translation.'


def wiktionary_extract_german(data: WiktionaryData):
    has_translations = data.text is not None and 'Ü-Tabelle' in data.text
    if not has_translations:
        raise NoTranslationEntryException(data)

    parsed_text: Wikicode = mwparserfromhell.parse(data.text)
    language: Optional[str] = None
    translations = defaultdict(lambda: set())

    for temp in parsed_text.filter_templates():
        temp: mwparserfromhell.nodes.template.Template
        if temp.name == 'Ü':
            lang_code = str(temp.params[0])
            for v in (str(k) for k in temp.params[1:]):
                if len(v) > 0:
                    translations[lang_code].add(v)
        elif temp.name == 'Sprache':
            language = str(temp.params[0])

    return data.title, language, dict(translations)


def wiktionary_extract_english(data: WiktionaryData):
    # print(data.text)
    has_translations = data.text is not None and 'trans-' in data.text
    if not has_translations:
        raise NoTranslationEntryException(data)
    parsed_text: Wikicode = mwparserfromhell.parse(data.text)
    language: Optional[str] = None
    translations = defaultdict(lambda: set())
    for temp in parsed_text.filter_templates():
        temp: mwparserfromhell.nodes.template.Template
        if temp.name == 't' or temp.name == 't+':
            lang_code = str(temp.params[0])
            for v in (str(k) for k in temp.params[1:]):
                if len(v) > 0 and v != 'm' and v != 'f' and v != 'n':
                    translations[lang_code].add(v)

    return data.title, language, dict(translations)

# def wiktionary_extract_english(data: WiktionaryData):
#     target_word = data.title
#     parsed_text = wtp.parse(data.text)
#     for section in parsed_text.sections:
#         if target_word in section.title:
#             pass
#     return 1


if __name__ == '__main__':

    for page in apply_filter(read_wiktionary(r'D:/Downloads/wiktionary/dewiktionary-20201101-pages-meta-current.xml')):
        if page.id != 555:
            continue
        print(page.id)
        print(page.title)
        print(page.text)
        break
        # try:
        #     pprint(wiktionary_extract_german(page))
        # except NoTranslationEntryException as e:
        #     print(str(e))
    #
    # print('-'*20)
    # for i, page in enumerate(apply_filter(read_wiktionary(r'D:/Downloads/wiktionary/enwiktionary-20201101-pages-meta-current.xml'))):
    #     try:
    #         wiktionary_extract_english(page)
    #     except NoTranslationEntryException as e:
    #         print(str(e))
    #     # pprint(wiktionary_extract_german(page))
    #     print('#'*30)
    #     if i == 20:
    #         break


