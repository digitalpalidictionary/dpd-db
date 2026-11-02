# Equivalence results

- (a) detector lists, slim against full: PASS (0 differences in 2589)
- (b) all_inflections, direct query against today: PASS (0 differences in 1627687)
- (c) word finder results, interned against today: PASS (0 differences in 193)
- (d) detector lists, split corpus against full: PASS (0 differences in 2589)
- (e) compact set: PASS (0 of 1627687 members answered no; 0 of 200001 non-members answered yes; 1627687 unique hashes)

## Lookup (task 1.3, check L5)

- Words in today's `all_inflections`: 1627687. Lookup keys with a non-empty `headwords`: 459013.
- In the set but not in the table: 1181761. Examples: ['', 'ababamhi', 'ababamhā', 'ababasmiṃ', 'ababasmā', 'ababassa', 'ababe', 'ababebhi', 'ababehi', 'ababena'].
- In the table but not in the set: 13087. Examples: ['AN1', 'AN1.1', 'AN1.1-10', 'AN1.10', 'AN1.100', 'AN1.101', 'AN1.102', 'AN1.103', 'AN1.104', 'AN1.105'].
- 1402 distinct words of CST `an1`: 1383 found by the set, 1382 by the table, 1401 answered the same by both.
- Time for 1402 words: set 0.0014 s, table 0.54 s (384 µs per query).
