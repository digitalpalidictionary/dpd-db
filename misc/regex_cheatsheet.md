# Regex Cheatsheet

A quick reference for regular expression syntax and patterns.

---

### Anchors

Anchors assert something about the string or the matching process's position. They don't match characters.

| Syntax | Description                               | Example                  |
| :----- | :---------------------------------------- | :----------------------- |
| `^`    | Start of the string (or line in multiline mode) | `^Hello` matches "Hello world" |
| `$`    | End of the string (or line in multiline mode)   | `world$` matches "Hello world" |
| `\b`   | Word boundary                             | `\bcat\b` matches "the cat"  |
| `\B`   | Non-word boundary                         | `\Bcat\B` matches "concatenate" |

---

### Character Classes

| Syntax | Description                                       |
| :----- | :------------------------------------------------ |
| `.`    | Any character except a newline                    |
| `\d`   | Any digit (0-9)                                   |
| `\D`   | Any non-digit                                     |
| `\w`   | Any word character (a-z, A-Z, 0-9, _)             |
| `\W`   | Any non-word character                            |
| `\s`   | Any whitespace character (space, tab, newline)    |
| `\S`   | Any non-whitespace character                      |
| `[abc]`| Matches `a`, `b`, or `c`                          |
| `[^abc]`| Matches any character except `a`, `b`, or `c`     |
| `[a-z]`| Matches any character from `a` to `z`             |

---

### Quantifiers

Specify how many times a character, group, or character class must be present.

| Syntax  | Description                               | Greediness |
| :------ | :---------------------------------------- | :--------- |
| `*`     | 0 or more times                           | Greedy     |
| `+`     | 1 or more times                           | Greedy     |
| `?`     | 0 or 1 time                               | Greedy     |
| `{n}`   | Exactly `n` times                         | Greedy     |
| `{n,}`  | `n` or more times                         | Greedy     |
| `{n,m}` | Between `n` and `m` times                 | Greedy     |
| `*?`    | 0 or more times                           | Lazy       |
| `+?`    | 1 or more times                           | Lazy       |

**Greedy** = Match as many characters as possible.
**Lazy** = Match as few characters as possible.

---

### Grouping and Capturing

| Syntax    | Description                                                              |
| :-------- | :----------------------------------------------------------------------- |
| `( ... )` | **Capturing Group:** Groups multiple tokens together and creates a capture group for extraction or back-referencing. |
| `(?: ... )`| **Non-Capturing Group:** Groups tokens but does not create a capture group. More efficient when you don't need the matched group's content. |
| `\1`, `\2` | **Backreference:** Matches the text of the first or second capturing group. |

---

## Lookarounds (Zero-Width Assertions)

Lookarounds check for a pattern before (lookbehind) or after (lookahead) the current position without including it in the final match. They are "zero-width," meaning they don't consume any characters.

### Positive Lookahead `(?=...)`

- **Asserts:** The text immediately *following* the current position must match the pattern inside `(?=...)`.
- **Use Case:** Match something that is followed by a specific pattern.

| Regex               | String          | Match   | Explanation                               |
| :------------------ | :-------------- | :------ | :---------------------------------------- |
| `\d+(?= USD)`      | `100 USD`, `50 EUR` | `100`   | Matches numbers that are followed by " USD". |
| `password:(?=.*\d)` | `password:abc123` | `password:` | Matches "password:" if it's followed by at least one digit somewhere. |

### Negative Lookahead `(?!...)`

- **Asserts:** The text immediately *following* the current position must **not** match the pattern inside `(?!...)`.
- **Use Case:** Match something that is *not* followed by a specific pattern.

| Regex             | String                | Match     | Explanation                                  |
| :---------------- | :-------------------- | :-------- | :------------------------------------------- |
| `admin(?!-local)` | `admin-local`, `admin-remote` | `admin` (in `admin-remote`) | Matches "admin" that is not followed by "-local". |
| `q(?!u)`          | `quit`, `Iraq`, `seq` | `q` (in `Iraq` and `seq`) | Matches a `q` that is not followed by a `u`. |

### Positive Lookbehind `(?<=...)`

- **Asserts:** The text immediately *preceding* the current position must match the pattern inside `(?<=...)`.
- **Use Case:** Match something that is preceded by a specific pattern.
- **Note:** Most regex engines require the pattern inside a lookbehind to be of a fixed length.

| Regex             | String          | Match | Explanation                               |
| :---------------- | :-------------- | :---- | :---------------------------------------- |
| `(?<=\$)\d+`      | `Price: $150`   | `150` | Matches numbers that are preceded by a "$". |
| `(?<=user: )\w+`  | `user: bodhi`   | `bodhi` | Matches a word that is preceded by "user: ". |

### Negative Lookbehind `(?<!...)`

- **Asserts:** The text immediately *preceding* the current position must **not** match the pattern inside `(?<!...)`.
- **Use Case:** Match something that is *not* preceded by a specific pattern.

| Regex               | String                | Match     | Explanation                                  |
| :------------------ | :-------------------- | :-------- | :------------------------------------------- |
| `(?<!non-)\w+ing`  | `non-breaking`, `running` | `running` | Matches a word ending in "ing" that is not preceded by "non-". |
| `(?<!http://)\w+\.com` | `http://a.com`, `b.com` | `b.com` | Matches a .com domain that is not preceded by "http://". |

---

### Common Flags

Flags modify the behavior of the entire regular expression.

| Flag | Description                                                     |
| :--- | :-------------------------------------------------------------- |
| `i`  | **Case-insensitive:** `a` will match `a` and `A`.               |
| `g`  | **Global:** Find all matches in the string, not just the first. |
| `m`  | **Multiline:** `^` and `$` will match the start/end of a line, not just the whole string. |
