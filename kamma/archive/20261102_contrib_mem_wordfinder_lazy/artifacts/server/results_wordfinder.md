## 4.2

$ git pull
Already up to date.

$ git log -1 --format=%h
267740fc

$ git status --porcelain
(no output — working tree clean)

## 4.3

| reading | rss MB (267740fc) | hwm MB (267740fc) | baseline rss MB (247a8429) | diff MB |
|---|---|---|---|---|
| plus15s_wf | 86.4 | 86.4 | - | - |
| warmup_done_wf | 774.1 | 774.1 | 943.3 | -169.2 |
| one_book_wf | 879.2 | 943.2 | 1045.7 | -166.5 |
| after_ctrlf_wf | 879.2 | 943.2 | - | - |

Note: the baseline one-book run used book mn with nothing to process, while the new run used book cp stopped after about ten words, so the one-book comparison is approximate.
