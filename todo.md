**Basic Requirements**
Indexer:
    [x] Tokens: all alphanumeric sequences in the dataset.
    [x] Stop words: do not use stopping, i.e. use all words, even the frequently occurring ones.
    [x] Stemming: use stemming for better textual matches. Suggestion: Porter stemming.
    [x] Important words: Words in bold, in headings (h1, h2, h3), and in titles should be treated as more important than the other words.


Search:
    [x] Your program should prompt the user for a query. 
    [x] Program will stem the query terms, look up your index, perform some calculations (see ranking below) and give out the ranked list of pages that are relevant for the query, with the most relevant on top. Pages should be identified by their URLs.
    [x] Ranking: at the very least, your ranking formula should include tf-idf scoring, and take the important words into consideration, but you should feel free to add additional components to this formula if you think they improve the retrieval. 
    [x] Key error: searching for key that dne throws key error


Extra Credit:
    [x] Implement a Web or GUI interface instead of a console one. (1 point for local GUI, 2 points for Web interface)
    [x] Detect and eliminate duplicate pages. (1 point for exact, 2 points for near)
        [x] Store SimHash fingerprints alongside documents
        [x] Compare only against documents with content length
    [ ] Add HITS and/or Page Rank to your ranking formula. (1.5 for HITS, 2.5 for PR)
    [ ] Implement an additional 2-gram and/or 3-gram indexing and use it during retrieval. (1 point)
    [ ] Enhance the index with word positions and use that information for retrieval. (2 points)
    [ ] Index anchor words for the target pages (1 point).


Search interface:
    [ ] The response to search queries should be 300ms. Ideally, it would be 100ms, or less, but you won’t be penalized if it’s higher (as long as it’s kept 300ms).


Operational constraints: 
    [x] Typically, the cloud servers/containers that run search engines don’t have a lot of memory, but they need to handle large amounts of data. As such, you must design and implement your programs as if you are dealing with very large amounts of data, so large that you cannot hold the inverted index all in memory. Your indexer must offload the inverted index hash map from main memory to a partial index on disk at least 3 times during index construction; those partial indexes should be merged in the end. 
    [x] Optionally, after or during merging, they can also be split into separate index files with term ranges. similarly, your search component must not load the entire inverted index in main memory. Instead, it must read the postings from the index(es) files on disk. The TAs will check that both of these things are happening.

------------------------------------------------------------------------------------------------------------------------------------------

**GOING THE EXTRA 7%!!!**
Misc:
    [x] Look into text indexing libraries such as Lucene, PyLucene, or ElasticSearch (might make our lives easier)
        > Decided to not use it

    [ ] Improve SimHash if possible but its the least of our priorities


Issues:
    [x] 'research' / 'comput' / 'scienc' tf_idf doesn't seem to save properly or work (?) Its all 0.0
        > Fixed: Sample data was too small

    [x] BeautifulSoup parse text gets a lot of date texts like "September 2019\nAugust 2019\nJuly 2019\nJune 2019\nMay 2019\nApril 2019\nMarch 2019\nFebruary 2019\nJanuary 2019\nDecember 2018\nNovember 2018\nOctober 2018\nSeptember 2018\nAugust 2018\nJuly 2018\nJune 2018" so what end up happening is that their simhash is too similar and they get marked as duplicates. Probably because of the below issue.
        > Fixed: Only parse <p>...</p> tags because that's the only real content
    
    [x] Need to improve SimHash, noticing some texts that are not similar at all are getting marked as duplicates (says 80% but like they are no where near alike so maybe the hashing is bad, or its just me picking the 2 different doc with so happens to be similar in hash)
        > Issue was stemming, since stemming made words into its root form, more words between the 2 docs were similar, hence the hash was similar. But since stemming is a requirement, we will have to live with it.
        > Can solve by increasing the threshold for similarity, or by using a better hashing algorithm

    [x] Important tags now have equal parts, ideally they should have different weights like 'title' will weight more (1.0), 'h1' (0.5) and 'h2' (0.25), etc...
        > Added

    [x] tf_idf may not be correct / Need references to see if it looks about right, pref from other students
        > Fixed

    [x] Size estimate to partition might be inaccurate (just the calculation, nothing wrong with the spliting I think) Need to further testing
        > Mixed up between text file ascii size and actual size of the data, resolved as it is not an issue

    [x] Real HTML pages found out there are full of bugs! Some of the pages in the dataset may not contain any HTML at all and, when they do, it may not be well formed. For example, there might be an open <strong> tag but the associated closing </strong> tag might be missing. While selecting the parser library for your project, please ensure that it can handle broken HTML.
        > BeautifulSoup can handle broken HTML, no longer an issue

    [ ] "XMLParsedAsHTMLWarning: It looks like you're parsing an XML document using an HTML parser. If this really is an HTML document (maybe it's XHTML?), you can ignore or filter this warning. If it's XML, you should know that using an XML parser will be more reliable. To parse this document as XML, make sure you have the lxml package installed, and pass the keyword argument `features="xml"` into the BeautifulSoup constructor."

    [ ] Deal with ascii encoding for some of the json (different format for db_ics, cs_uci)