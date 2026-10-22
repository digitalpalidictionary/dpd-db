"""Hostile patterns must stay inside a time and memory budget (issue #268).

Each pattern runs in its own child process with a hard memory cap, against
~21 KB of text, so a failure here cannot take the test machine down.
"""

import json
import resource
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

PATTERNS = [
    "(a+)+b",
    "^(a|aa)+$",
    "(.*)*x",
    "(?:.*)*(?:.*)*y",
    "(x+x+)+y",
    "(?=(a+)+b)",
    "(?<=a{500})b",
    "(?:(?:a|b)*)*c",
    r"\p{L}{1000}",
    r"(\w+\s?)*$",
    "((((((((((a*)*)*)*)*)*)*)*)*)*)*b",
    "(?R)?",
    r"(.+)\1+z",
    "(?i)(?:a|ab|abc)*d",
    "^(.|.)+[Z!]",
    "(?:a{1500}){1500}",
    "(?:a{3000}){3000}",
    "(?:(?:a{100}){100}){100}",
    "(?:a?){1000}a{1000}",
    "(" * 900 + "a" + ")" * 900,
    "(" * 4000 + "a" + ")" * 4000,
    "a" * 5000,
    "[a-z]{65535}[a-z]{65535}",
    "(?:|a)*b",
    "(?:a|b|c|d|e|f|g|h)*{3,5}z",
    "x{99999999999}",
    "(?R)",
    "(?0)*",
    "(a)(?1)*",
    "(?P<x>a|b)(?&x)*",
    "(?P<x>a|b)(?P>x)*",
    r"(?P<x>a|b)\g<x>*",
    "(?(DEFINE)(?<x>a))(?&x)*z",
    "(?<=(?:a+)+)b",
    "(?:dhamma){e<=1000}",
    "(?:dhamma){i<=100000}",
    "(?:dhamma){1<=e<=50,s<=50}",
    "(?b)(?:dhamma){e<=5}",
    "(?e)(?:dhamma){e<=5}",
    r"\X*z",
    "(?:(?:a|b)*)*(?:(?:c|d)*)*e",
    "(?<!(?:a|b)+)z",
    "(?:qzxwv){e<=4}",
    "(?:qzxwv){s<=1000,i<=1000,d<=1000}",
    "(?r)(?:qzxwv){e<=3}",
]

CHILD = """
import json, resource, sys, time
from tools.search_deadline import SearchStopped, regex_deadline, regexp_search

pattern = json.loads(sys.argv[1])
text = "dhamma " * 3000 + "!"
before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024
start = time.monotonic()
try:
    with regex_deadline(2.0):
        outcome = "match" if regexp_search(pattern, text) else "no match"
except SearchStopped:
    outcome = "stopped"
print(json.dumps({
    "outcome": outcome,
    "sec": round(time.monotonic() - start, 2),
    "mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024 - before,
}))
"""


def cap_child_memory() -> None:
    resource.setrlimit(resource.RLIMIT_AS, (1_200_000_000, 1_200_000_000))


def run_one(pattern: str) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, "-I", "-c", CHILD, json.dumps(pattern)],
        capture_output=True,
        text=True,
        timeout=30,
        preexec_fn=cap_child_memory,
    )
    if result.returncode != 0:
        return {"outcome": f"CRASHED: {result.stderr.strip()[-80:]}", "sec": 0, "mb": 0}
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def outcomes() -> dict[str, dict[str, object]]:
    with ThreadPoolExecutor(max_workers=3) as pool:
        return dict(zip(PATTERNS, pool.map(run_one, PATTERNS)))


@pytest.mark.parametrize("pattern", PATTERNS, ids=[p[:30] for p in PATTERNS])
def test_hostile_pattern_stays_inside_the_budget(
    outcomes: dict[str, dict[str, object]], pattern: str
) -> None:
    outcome = outcomes[pattern]
    assert outcome["outcome"] in ("match", "no match", "stopped"), outcome
    assert float(str(outcome["sec"])) < 6, outcome
    assert int(str(outcome["mb"])) < 300, outcome
