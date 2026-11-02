# Expected numbers for the three fixture files

Worked by hand from the values in the fixtures. All in MB. The laptop fixture has
three runs per point; `corpus` has deltas 300, 300, 400 (the only flagged spread).

- Isolated deltas: bare 30, imports 100, db_manager 10, initialize_db 50, corpus 300,
  inflections_lists 40, relationship_detector 60, wordfinder 200, ai_manager 20,
  bold_search 5, spellchecker 15. Sum = 830.
- Staircase total 795, so the interaction gap = 795 − 830 = −35.
- Books: 80, 70, 60, 50, so one book = median = 65. Four in one process: 375 − 130 = 245.
- Server staircase total 700. Server warm RSS = the larger of 1000 and 40 = 1000.
  Raw unbuilt remainder = 1000 − 700 = 300. The app warm-up does not build the
  inflection lists (staircase step 510 − 475 = 35), so the adjusted remainder
  = 1000 − (700 − 35) = 335, which is above 20 % of 1000.
- Server book step = one_book 1100 − warm 1000 = 100. Four books on the server
  = 100 + (245 − 65) = 280.
- Read-only rows (bare, imports, corpus, inflections_lists, relationship_detector,
  wordfinder, ai_manager) = 30 + 100 + 300 + 40 + 60 + 200 + 20 = 750, of which
  40 are the inflection lists, so 710 at warm-up.
  Per-user rows (db_manager, initialize_db, bold_search, spellchecker) = 10 + 50 + 5 + 15 = 80.
- Today = 1066 + N × (1000 + book step): N=8: 9866 (one book, step 100),
  11306 (four, step 280). N=16: 18666, 21546.
- Option E = 1066 + 710 + 40 + books + N × (80 + 335): N=8: 5201 (books 65),
  5381 (books 245). N=16: 8521, 8701.
- B = 200 + 20 + 5 + 60 = 285. C = 40. D = 200. E saves 750 × (N − 1): 5250 at 8, 11250 at 16.
- Phase steps: db load 600 − 300 = 300; tabs and managers 1000 − 600 = 400; one book 100;
  reloads 80, 120, 30.

KEY e_16_1=8521.0
KEY e_16_4=8701.0
KEY e_8_1=5201.0
KEY e_8_4=5381.0
KEY flag_ai_manager=no
KEY flag_bare=no
KEY flag_bold_search=no
KEY flag_corpus=yes
KEY flag_db_manager=no
KEY flag_imports=no
KEY flag_inflections_lists=no
KEY flag_initialize_db=no
KEY flag_relationship_detector=no
KEY flag_spellchecker=no
KEY flag_wordfinder=no
KEY four_books=245.0
KEY interaction_gap=-35.0
KEY iso_ai_manager=20.0
KEY iso_bare=30.0
KEY iso_bold_search=5.0
KEY iso_corpus=300.0
KEY iso_db_manager=10.0
KEY iso_imports=100.0
KEY iso_inflections_lists=40.0
KEY iso_initialize_db=50.0
KEY iso_relationship_detector=60.0
KEY iso_spellchecker=15.0
KEY iso_wordfinder=200.0
KEY laptop_staircase_total=795.0
KEY one_book=65.0
KEY opt_B=285.0
KEY opt_C=40.0
KEY opt_D=200.0
KEY opt_E_16=11250.0
KEY opt_E_8=5250.0
KEY per_user=80.0
KEY server_staircase_total=700.0
KEY server_warm_rss=1000.0
KEY shared_read_only=750.0
KEY step_db_loaded=300.0
KEY step_one_book=100.0
KEY step_reload1=80.0
KEY step_reload2=120.0
KEY step_reload3=30.0
KEY step_warmup_done=400.0
KEY sum_isolated=830.0
KEY today_16_1=18666.0
KEY today_16_4=21546.0
KEY today_8_1=9866.0
KEY today_8_4=11306.0
KEY unbuilt_over_20pct=yes
KEY unbuilt_remainder=335.0
KEY unbuilt_remainder_raw=300.0
KEY server_book_step=100.0
KEY four_books_server=280.0
