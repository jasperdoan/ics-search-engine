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


Search interface:
    [x] The response to search queries should be 300ms. Ideally, it would be 100ms, or less, but you won’t be penalized if it’s higher (as long as it’s kept 300ms).


Operational constraints: 
    [x] Typically, the cloud servers/containers that run search engines don’t have a lot of memory, but they need to handle large amounts of data. As such, you must design and implement your programs as if you are dealing with very large amounts of data, so large that you cannot hold the inverted index all in memory. Your indexer must offload the inverted index hash map from main memory to a partial index on disk at least 3 times during index construction; those partial indexes should be merged in the end. 
    [x] Optionally, after or during merging, they can also be split into separate index files with term ranges. similarly, your search component must not load the entire inverted index in main memory. Instead, it must read the postings from the index(es) files on disk. The TAs will check that both of these things are happening.


------------------------------------------------------------------------------------------------------------------------------------------
**Improvements Ideas**
    [x] Query Optimization: Optimize how you handle queries. For instance, if you have longer queries, try to reduce the number of postings lists you need to access by using techniques like query rewriting or term-at-a-time processing.
        > Ditched since its only applicable to Boolean search AND/OR need excessive req like a NLP model

    [x] Algorithmic Improvements: Consider using more advanced algorithms for ranking and retrieval. Techniques like BM25 or TF-IDF can be optimized for faster computation.
        > Wtf is BM25, tf-idf is already implemented but idk if we'll cover BM25

    [x] Cache
        > Works like a charm, thanks Homi

    [x] Uses sparse matrix for tf-idf calculations / computation
        > More memory efficient, makes it faster to compute and retrieve data

    [x] Make more partials range indexes (Sharding): Instead of a-c, d-f, etc... lets just do 1 term per json or 2 terms per json. I've noticed a significant time improvement from purely reading the full index vs partial. So maybe it might shave off more time for us who knows.
        > Done

    [x] Optimize Data Structures: JSON is flexible but can be slow to parse. Consider using a more efficient binary format for storing your postings if performance is critical.
        > Tried csv, slower even though reading is faster, parsing it back to dict is slow. 
        > Pickle overtook json! We should look at binary format now, since Pickle is specifically designed for serializing and deserializing Python objects, there's no parsing overhead, which saves time.
            - 'machine learning'                            query time: 0.645s -> 0.359s
            - 'research'                                    query time: 0.625s -> 0.374s
            - 'master of computer science'                  query time: 1.303s -> 1.143s
            - 'master of software engineering'              query time: 1.375s -> 0.709s 
            - 'cristina lopes'                              query time: 0.713s -> 0.372s
            - 'machine learning and its impact on society'  query time: 1.753s -> 0.922s

    [x] Cristina peek()


------------------------------------------------------------------------------------------------------------------------------------------
**GOING THE EXTRA 7%!!!**
Extra Credit:
    [x] Implement a Web or GUI interface instead of a console one. (1 point for local GUI, 2 points for Web interface)

    [x] Detect and eliminate duplicate pages. (1 point for exact, 2 points for near)

    [x] Enhance the index with word positions and use that information for retrieval. (2 points)

    [x] Cosine Similarity

    [x] Add HITS and/or Page Rank to your ranking formula. (1.5 for HITS, 2.5 for PR)
        [x] HITS: Hyperlink-Induced Topic Search
        [x] PR: PageRank

    [ ] Implement an additional 2-gram and/or 3-gram indexing and use it during retrieval. (1 point)

    [ ] Index anchor words for the target pages (1 point).

------------------------------------------------------------------------------------------------------------------------------------------
**TODO/ISSUES**
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

    [x] https://www.ics.uci.edu/~ziv/ooad/intro_to_se/sld027.htm site is just horrible and not sure what it is reading but appears on query "master of computer science" alot, but has nothing to do with mse. Was considering to be low value and unreadable but that link was the exception. https://www.ics.uci.edu/~ziv/ooad/intro_to_se/tsld027.htm is a lot better but still doesn't show up alot. I'm assuming the former site is only able to spit out the title (3 words), and so it gives massive point boost for tf-idf. That's why it shows up high for MSE queries
        > Adjusted weights + term matching boost to fix this issue

    [x] Certain sites appears #1 search for non-conventional words / Encountering a situation where a page with a comprehensive word list is being ranked highly for queries involving rare or unique words. This behavior is literally "keyword stuffing" from quiz1, this really influence the tf-idf ranking if the word is rare in other documents. Listed below:
        - https://www.ics.uci.edu/~kay/wordlist.txt 
        - https://ics.uci.edu/~kay/courses/h22/hw/DVD.txt 
        - https://ics.uci.edu/~kay/courses/h22/hw/wordlist-random.txt
        > End up ignoring any .txt files, since they are not HTML and are not relevant to the search

    [x] Improve SimHash if possible but its the least of our priorities
        > No longer applicable

    [ ] "XMLParsedAsHTMLWarning: It looks like you're parsing an XML document using an HTML parser. If this really is an HTML document (maybe it's XHTML?), you can ignore or filter this warning. If it's XML, you should know that using an XML parser will be more reliable. To parse this document as XML, make sure you have the lxml package installed, and pass the keyword argument `features="xml"` into the BeautifulSoup constructor."

    [ ] Deal with ascii encoding for some of the json (different format for db_ics, cs_uci)

    [ ] Need better word positioning, rn its not as accurate I think its because of the weird tokenizing that's screwing it up

    [ ] Cristina's tf-idf way in lecture, she log(tf) which kinda go against the formula but her explanation makes sense. Might need to do a separate index and comare if it really affects the search, and does it even matter.

    [ ] “url” : contains the URL of the page. (ignore the fragment part, if you see it)