#!/usr/bin/env python3
"""Every number a document claims about this repo, checked against the repo.

Written because the counts went stale five times in one day — `CLAUDE.md`,
`README.md` and a wiki page each carried "seven of eight sourcing topics",
"one real actuator record" and "no robot record yet" past the point where
those were true, and every one was found by a person reading rather than by
anything running.

`CLAUDE.md` already states the rule this enforces:

    do not leave a status claim standing after the code has moved past it —
    this section said "no code" for exactly as long as that was true.

A rule that only holds when somebody remembers it is the case where somebody
remembered. These claims are all derivable, so deriving them is cheap and the
failure is loud.

Test counts cannot be derived without running the suites, so CI passes them in
with --python-tests and --rust-tests. Run without them, the script checks
everything else and says which checks it skipped rather than passing quietly.

    python scripts/check_claims.py
    python scripts/check_claims.py --python-tests 162 --rust-tests 36

Stdlib only, like the rest of `scripts/`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ("CLAUDE.md", "README.md")

ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = {20: "twenty", 30: "thirty", 40: "forty", 50: "fifty", 60: "sixty",
        70: "seventy", 80: "eighty", 90: "ninety"}


def spelled(n: int) -> str | None:
    """The English for n, matching how these documents write their counts.

    None above 99: these documents write "twenty-four ADRs" but "162 Python
    tests", and inventing a spelling nobody uses would make the checker demand
    prose the repo does not write.
    """
    if n < 20:
        return ONES[n]
    if n > 99:
        return None
    tens, ones = divmod(n, 10)
    base = TENS[tens * 10]
    return base if ones == 0 else f"{base}-{ONES[ones]}"


def forms(n: int) -> set[str]:
    return {str(n)} | ({w} if (w := spelled(n)) else set())


# Only a NUMBER in front makes a phrase a claim. Without this the patterns
# matched "python scripts/validate.py" as a claim of "python scripts", and
# "the Rust tests" as a claim of "the". Longest-first so "twenty-four" wins
# over "twenty".
NUM = "(?:" + "|".join(
    [r"\d+"] + sorted((spelled(i) for i in range(100)), key=len, reverse=True)
) + ")"


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.skipped: list[str] = []
        self.checked = 0

    def claim(self, doc: str, label: str, pattern: str, actual: int) -> None:
        """A count claimed in prose must equal the count derived from the repo."""
        text = (ROOT / doc).read_text(encoding="utf-8")
        found = re.findall(pattern, text, re.IGNORECASE)
        if not found:
            return  # the document does not make this claim; that is allowed
        self.checked += 1
        ok = forms(actual)
        for raw in found:
            if raw.lower() not in ok:
                self.failures.append(
                    f"{doc}: claims {raw!r} {label}, repo has {actual} "
                    f"({' or '.join(sorted(ok))})")

    def forbid(self, doc: str, phrase: str, when: bool, because: str) -> None:
        """A phrase that a change to the repo has made false."""
        if not when:
            return
        self.checked += 1
        text = (ROOT / doc).read_text(encoding="utf-8")
        if phrase.lower() in text.lower():
            self.failures.append(f"{doc}: says {phrase!r}, but {because}")


def count_records(kind: str) -> int:
    d = ROOT / "data" / kind
    return len(list(d.glob("*.json"))) if d.is_dir() else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--python-tests", type=int, default=None)
    ap.add_argument("--rust-tests", type=int, default=None)
    args = ap.parse_args()

    adrs = len(re.findall(r"^## ADR-\d+",
                          (ROOT / "DECISIONS.md").read_text(encoding="utf-8"),
                          re.MULTILINE))
    schemas = len(list((ROOT / "schema").glob("*.schema.json")))
    # No self-exclusion: a script that leaves itself out of its own count is
    # the same defect it exists to catch, wearing a better disguise.
    scripts = len(list((ROOT / "scripts").glob("*.py")))
    robots = count_records("robots")
    actuators = count_records("actuators")

    r = Report()
    for doc in DOCS:
        r.claim(doc, "ADRs", rf"({NUM}) ADRs", adrs)
        r.claim(doc, "schemas", rf"({NUM}) schemas", schemas)
        r.claim(doc, "scripts", rf"({NUM}) (?:stdlib )?scripts", scripts)
        r.claim(doc, "records in data/", rf"holds ({NUM}) real records?",
                robots + actuators)
        # "two real actuator records" outlived ADR-0024 splitting the clone
        # into its own record, and the forbid() below could not see it — a
        # forbid pins one phrase, and the phrase had moved on. Any counted
        # claim about actuator or robot records is now checked as a count.
        r.claim(doc, "actuator records", rf"({NUM}) (?:real )?actuator records?",
                actuators)
        r.claim(doc, "robot records", rf"({NUM}) (?:real )?robot records?",
                robots)
        if args.python_tests is not None:
            r.claim(doc, "Python tests", rf"({NUM}) Python tests", args.python_tests)
        if args.rust_tests is not None:
            r.claim(doc, "Rust tests", rf"({NUM}) Rust tests", args.rust_tests)

        # The three that actually went stale today, as phrases rather than counts.
        r.forbid(doc, "no robot record yet", robots > 0,
                 f"data/robots/ holds {robots}")
        r.forbid(doc, "one real actuator record", actuators != 1,
                 f"data/actuators/ holds {actuators}")
        r.forbid(doc, "holds one real record", actuators + robots != 1,
                 f"data/ holds {actuators + robots}")

    if args.python_tests is None:
        r.skipped.append("Python test count (pass --python-tests)")
    if args.rust_tests is None:
        r.skipped.append("Rust test count (pass --rust-tests)")

    print(f"derived: {adrs} ADRs, {schemas} schemas, {scripts} scripts, "
          f"{robots} robot(s), {actuators} actuator(s)")
    print(f"{r.checked} claim(s) checked across {len(DOCS)} document(s)")
    for s in r.skipped:
        print(f"  SKIPPED {s}")
    for f in r.failures:
        print(f"  STALE   {f}")

    if r.failures:
        print("\nA status claim outlived what it described. Update the document —\n"
              "the number is not the point, the habit of leaving them behind is.")
        return 1
    print("no stale claim found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
