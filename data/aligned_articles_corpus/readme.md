Origin: https://linguatools.org/tools/corpora/wikipedia-comparable-corpora/
(A Backup of the Website is stored alongside the readme.md)

Dropbox Link: https://www.dropbox.com/scl/fi/808m6tuztu6w8f1e5704r/wikicomp-2014_deen.xml.bz2?rlkey=pyh6nd8ydsdcih1yg91y62wbb&e=1&dl=0

## File Format:

The XML file’s root element is wikipediaComparable. Its attribute name contains the language pair. Then follows a header which has two daughter nodes, both of type wikipediaSource. Their attributes give the languages and the names of the two source Wikipedia Monolingual Corpora’s XML files.

The header is followed by n elements of type articlePair, which have an attribute id with a unique identification number. Each articlePair encloses two articles, one from the first language Wikipedia, and a corresponding one from the second language Wikipedia. Corresponding means that both articles are linked via a crosslanguage link (in any direction). „Deep“ links that link an article to a section of a target article have been replaced by a link to the whole article (see note on crosslanguage_links in the XML format description on the monolingual corpora page). Each article has a number of categories and a content. The categories are copied from the respective Wikipedia Monolingual Corpora XML files, as is the content. The content therefore includes p and h tags marking paragraphs and headings, and also links and tables (see the XML format description on the monolingual corpora page).

<wikipediaComparable name="nl-ro">
   <header>
      <wikipediaSource language="nl" name="nlwiki-20140804-corpus.xml"/>
      <wikipediaSource language="ro" name="rowiki-20140729-corpus.xml"/>
   </header>
   <articlePair id="1">
      <article lang="nl" name="Les Fleurs du mal">
         <categories name="Dichtbundel|Franse literatuur|19e-eeuwse literatuur"/>
         <content>
            <p>Les Fleurs du mal (De bloemen van het kwaad) is de belangrijkste dichtbundel van de Franse dichter Charles Baudelaire.</p>
            ...
         </content>
      </article>
      <article lang="ro" name="Florile răului">
         <categories name="Cărți apărute în 1857"/>
         <content>
            <p>Florile răului este o culegere de poezii ale poetului francez Charles Baudelaire.</p>
            ...
         </content>
      </article>
   </articlePair>
   ...
</wikipediaComparable>
