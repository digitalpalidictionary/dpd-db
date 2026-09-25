# Jev quickstart

Jev is a "System One" decision model from TypeSafe. It does not write text. You send it a
**state** (the thing to judge) and one or more typed **questions**, and it returns a
probability for each answer. It is fast (about 0.3 s) and very cheap (about $0.00001 a call).

Everything below was checked with live calls on 2026-09-23 unless marked *(docs only)*.

## Where it lives

- Model page: https://openrouter.ai/~typesafe/jev-latest
- Endpoint: `POST https://openrouter.ai/api/alpha/decisions`
  - `POST https://openrouter.ai/api/v1/systemone` also works and gives the same result.
- Auth: the normal OpenRouter key as a Bearer token, from `config.ini` → `[apis] openrouter`
  (read it with `config_read("apis", "openrouter")` from `tools/configger.py`). No key → HTTP 401.
- Model ids that work: `~typesafe/jev-latest` (the tilde matters) and `typesafe/jev-1.13`.
  Both currently resolve to `typesafe/jev-1.13-20260917`.
- Model ids that fail: `typesafe/jev-latest` (no tilde) → "does not exist".

Traps:

- Jev is **not** listed in `GET /api/v1/models`. That list only covers text models.
- Do **not** send it to `/api/v1/chat/completions`. That returns
  "is a decisions model and cannot be used with the chat/completions endpoint".
- There is no system prompt, no messages list, and no temperature. Only `model`, `state`, `questions`.
- Context window: 32 000 tokens. Price: $0.042 per million input tokens, output is free.
  Each call has a fixed overhead of about 270 input tokens.

## Request shape

```json
{
  "model": "~typesafe/jev-latest",
  "state": "any string, object, or array",
  "questions": {
    "<your_key>": { "type": "noul | choice | score", "instructions": "...", "criteria": ... }
  }
}
```

- `state` can be a string, a JSON object, or a JSON array. All three were tested.
- `questions` is an object. Each key is your own name for the answer.
- Put many questions in one call. Jev answers them in parallel, so extra questions
  barely change the response time. This is cheaper than one call per question.

## The three question types

### 1. `noul` — yes / no

Returns the probability that the statement is true. `criteria` is optional.

```json
"is_urgent": {
  "type": "noul",
  "instructions": "This message needs attention right now",
  "criteria": {
    "true": "outage, data loss, customer blocked",
    "false": "question, feature request, cosmetic issue"
  }
}
```

Answer:

```json
"is_urgent": { "type": "noul", "noul": 0.91 }
```

Tips *(docs)*:

- Ask one thing per noul. Phrase it so that a high value means yes. A plain statement works
  as well as a question.
- Use `criteria` when the line between yes and no is subtle. In our tests it helped a little.
- Your code picks the threshold. Raise it when a false "yes" is costly. Lower it when a
  missed "yes" is costly. Send the middle band to a human or a bigger model.

### 2. `choice` — pick one option

`criteria` is **required** and is an object: option name → description.

```json
"team": {
  "type": "choice",
  "instructions": "Which team owns this ticket?",
  "criteria": {
    "billing": "charges, invoices, payment problems",
    "infra": "servers, deploys, outages",
    "sales": "pricing questions"
  }
}
```

Answer:

```json
"team": {
  "type": "choice",
  "choice": "infra",
  "probabilities": { "billing": 0, "infra": 1, "sales": 0 },
  "confidence": 1
}
```

`confidence` shows how much the probability sits on a single option.

### 3. `score` — rate on ordered levels

`criteria` is **required** and is an array of levels, lowest first. Describe each level
as a concrete situation, not an abstract degree ("blocking, no workaround", not "high").

```json
"severity": {
  "type": "score",
  "instructions": "How severe is the reported issue?",
  "criteria": ["cosmetic", "degraded, workaround exists", "blocking, no workaround"]
}
```

Answer:

```json
"severity": {
  "type": "score",
  "score": 1.99,
  "legend": { "0": "cosmetic", "1": "degraded, workaround exists", "2": "blocking, no workaround" },
  "probabilities": { "0": 0, "1": 0, "2": 1 },
  "confidence": 0.99
}
```

`score` is the expected level, a float from 0 to (number of levels − 1).

### Full response

```json
{
  "model": "typesafe/jev-1.13-20260917",
  "answers": { "...": "one entry per question key" },
  "usage": { "input_tokens": 407, "output_tokens": 68, "cost": 0.000017094 },
  "id": "gen-dec-...",
  "provider": "TypeSafe"
}
```

An invalid type (for example `"boolean"`) or a missing `criteria` returns HTTP 400 with a
validation message that names the exact path, such as `questions.team.criteria`.

## Python example

```python
import requests

from tools.configger import config_read

URL = "https://openrouter.ai/api/alpha/decisions"


def jev(state: str | dict | list, questions: dict) -> dict:
    key = config_read("apis", "openrouter")
    r = requests.post(
        URL,
        headers={"Authorization": f"Bearer {key}"},
        json={"model": "~typesafe/jev-latest", "state": state, "questions": questions},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["answers"]


answers = jev(
    "The deploy failed and customers see 500s.",
    {"urgent": {"type": "noul", "instructions": "This needs attention now"}},
)
print(answers["urgent"]["noul"])
```

For bulk work, run calls in a thread pool. Eight workers did 200 calls in about 19 s with no
rate-limit errors. About 3% of calls (12 of ~400 in one run) failed with a dropped
connection (`requests.ConnectionError`, "Remote end closed connection without response"),
not an HTTP error. Catch that exception and retry. Checking only `r.ok` does not cover it.

## Good use cases

Jev suits coarse, clear-cut decisions that code must make many times:

- Routing: send a request to the right handler, team, or model (`choice`).
- Triage: is a message urgent, spam, off-topic, or a complaint (`noul`).
- Gating: is a request safe to run before a tool call (`noul` + threshold).
- Rating: how severe, how complete, how relevant (`score`).
- Fan-out: ask many speculative questions in one call and let code use the relevant ones.

## Poor use cases

- Anything that needs text written back: summaries, corrections, translations.
- Fine judgements on short text where the "wrong" and "right" cases look almost the same.

### Worked example: DPD proofreading filter (rejected)

Issue #196. The idea was to ask Jev "does this `meaning_1` need spelling or grammar
correction?" and send only the "yes" entries to the proofreading LLM
(`tools/proofreader.py`). The answer key was the earlier LLM proofreading run: entries in
`tools/proofreader.tsv` counted as errors, and checked entries left alone counted as clean.

Best result: one noul listing every error type (typos, American spelling, -ise vs -ize,
wrong word form, missing hyphen, missing Oxford comma), plus `criteria` saying that
semicolon lists, brackets, abbreviations and Pāḷi words are normal. Tested on 80 errors
and 320 clean entries:

| Errors caught | Clean entries also sent on |
|---|---|
| 80% | 40% |
| 90% | 67% |
| 95% | 77% |

The median score for an error was 0.31, and for a clean entry 0.19. The two groups
overlap too much to split safely. Separate narrow questions (typo / American spelling /
grammar / hyphen) did worse. The filter was dropped: it misses real errors, and the
proofreader's cache already limits each run to new or changed entries, so the saving
would be a few cents.

### Two more DPD tests (2026-09-23, also rejected)

Both used the live `dpd.db` as the answer key.

- **Bahubbīhi detection** (replacing the word rules in
  `db_tests/single/fixme/test_bahubbihis.py`). One noul on lemma + construction +
  meaning_1, with criteria "who has X / with X / having X" vs "X-ing / made of X / done by
  X". Tested on 100 adjective compounds typed bahubbīhi and 100 of other types. The
  who/whose/which/with/having word rule got 56% right. Jev got 64% at threshold 0.5
  (caught 52, false alarms 25). Slightly better, but not good enough to trust.
- **Homonym picking** (which same-spelled headword a word in a sentence belongs to). One
  choice question, options = each homonym's pos + meaning_1, state = its `example_1`
  with the word in bold. On 200 cases Jev picked right 60% of the time, against 41% for a
  random guess. Even at confidence ≥ 0.95 (34 cases) it was right only 79%.

Pattern: Jev does well on clear-cut English decisions and poorly on fine Pāḷi grammar
and meaning. DPD's high-volume work is almost all the second kind.
