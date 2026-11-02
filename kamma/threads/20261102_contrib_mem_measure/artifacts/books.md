# Books (Phase 0.2, 2026-11-02)

Source: `sutta_central_books` in `gui2/books.py:78`. Pass1Auto sets `cst_books` from the chosen book (`gui2/pass1_auto_controller.py:123`) and loads `make_cst_text_list(self.cst_books, dedupe=True)` (`:290`). CST files come from `cst_texts` in `tools/pali_text_files.py`, in `resources/dpd_submodules/cst/romn_txt`. SC bytes = every file under the book's pali and english folders in `resources/sc-data/sc_bilara_data`. No CST file is missing for any book.

| Book | SC bytes | CST books used | CST bytes | Total bytes |
|---|---|---|---|---|
| an | 7,639,697 | an1-an11 | 3,319,413 | 10,959,110 |
| sn | 6,943,882 | sn1-sn5 | 2,905,986 | 9,849,868 |
| mn | 5,479,751 | mn3, mn2, mn1 | 2,682,067 | 8,161,818 |
| vin3&4 | 5,576,526 | vin3, vin4 | 2,172,752 | 7,749,278 |
| jaa | 0 | kn14a | 6,186,144 | 6,186,144 |
| vin1&2 | 4,127,641 | vin1, vin2 | 1,685,542 | 5,813,183 |
| dn | 3,280,442 | dn3, dn1, dn2 | 1,567,758 | 4,848,200 |
| vin5 | 2,235,460 | vin5 | 730,802 | 2,966,262 |
| ja | 1,537,998 | kn14 | 1,038,437 | 2,576,435 |
| vin-bi | 1,250,751 | vin2 | 899,439 | 2,150,190 |
| dna | 0 | dna | 2,043,121 | 2,043,121 |
| dhpa | 0 | kn2a | 1,901,656 | 1,901,656 |
| nidd1&2 | 0 | kn15, kn16 | 1,436,136 | 1,436,136 |
| snp | 665,976 | kn5 | 230,759 | 896,735 |
| th | 678,650 | kn8 | 194,004 | 872,654 |
| ud | 465,990 | kn3 | 223,429 | 689,419 |
| kva | 0 | kva | 669,374 | 669,374 |
| iti | 360,428 | kn4 | 131,725 | 492,153 |
| thi | 253,502 | kn9 | 76,292 | 329,794 |
| dhp | 193,923 | kn2 | 61,795 | 255,718 |
| cp | 153,275 | kn13 | 48,432 | 201,707 |
| khp | 36,416 | kn1 | 13,699 | 50,115 |

22 rows = the 22 entries of `sutta_central_books`.

## The four chosen (largest totals)
Largest first, as `books_cumulative` opens them: `an`, `sn`, `mn`, `vin3&4`.
Driver argument: `--books "an,sn,mn,vin3&4"` (quote it: `&` is a shell character).

## Server book
`mn` (third largest; Pass1Auto choice, `gui2/books.py:114`). If the lean server lacks its files, use `sn`.

## Files the server needs for `mn`
- SC pali folder: `resources/sc-data/sc_bilara_data/root/pli/ms/sutta/mn` and the English folder `resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/mn` (both read from `gui2/books.py:117-118`).
- CST: `resources/dpd_submodules/cst/romn_txt/s0201m.mul.txt`, `s0202m.mul.txt`, `s0203m.mul.txt`.
