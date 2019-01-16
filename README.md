# tamilvu-etymdict-scraper
Scrape words and word meanings form TamilVU [http://stream1.tamilvu.in/etytamildict/TamilDemo.aspx]


### Building the dict
![Snapshot of word entry Karandai](/images/snap-karandai.png)
     The html of the snapshot it not well structured. It is just a <span> consisting of various strings, <font> and <br> to give the look of structured appearance. so when parsing,

    1. the red colored segment -> word_sense
    2. blue is either -> english_meaning or pronounciation
    3. green is part of speech
    but the rest don't have any clear structure, so I had come up with hand written rules like

    i. if it is italic and starts with '(' it is a reference,
    ii. if it starts with '[' it is etymology

    and such.

    I looked through few words entries and wrote the parser. what ever part which don't fall under the rules, will be collected and dumped again as the last entry 
