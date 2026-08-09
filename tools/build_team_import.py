#!/usr/bin/env python3
"""Generate a PlayMetrics Import Teams CSV for AYSO Region 58 from enrollment counts.

Team count per division is derived as ceil(enrollments / roster_size), so the
shells you import match the demand you actually have. Feed it enrollment numbers
from the Region 58 Portal and it emits a file matching PlayMetrics' sample-teams
template exactly, column for column.

    python build_team_import.py --enrollments enrollments.csv --out teams.csv

enrollments.csv is two columns, division and count:

    division,enrolled
    06U Boys,48
    06U Girls,31
    10U Boys,84

Divisions absent from the enrollment file are skipped, so you can run it early
with partial numbers and re-run as registration fills.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

# PlayMetrics sample-teams template, in order. Do not reorder or drop any of
# these -- the import errors out if a header is missing, even when the value
# below it is blank.
COLUMNS = [
    "season", "name", "acct_code", "gender", "level", "birth_year", "age_group",
    "minimum_age", "coach_first_name", "coach_last_name", "coach_email",
    "coach_mobile", "num_starting_players",
]

SEASON = "Fall 2026"          # must match the PlayMetrics Season name exactly
LEVEL = "Core"                # CONFIRM: sample template showed Classic / Academy

# Region 58 Fall 2026 plan. roster is our own planning cap (PlayMetrics may not
# enforce it -- see Phase 3 of the Team & Player Roster Setup guide).
# starters is num_starting_players: players on the field at kickoff, NOT roster
# size. Inferred from our roster sizes; CONFIRM against AYSO playing formats
# before importing.
PLAN = {
    # age_group: (roster, starters)
    "06U": (6, 4),
    "07U": (7, 5),
    "08U": (7, 5),
    "10U": (9, 7),
    "12U": (12, 9),
    "14U": (14, 11),
    "16U": (14, 11),
    "19U": (22, 11),
}

GENDERS = {"Boys": "M", "Girls": "F"}


def parse_division(label: str) -> tuple[str, str]:
    """'10U Boys' -> ('10U', 'Boys'). Raises on anything unexpected."""
    parts = label.strip().split()
    if len(parts) != 2 or parts[0] not in PLAN or parts[1] not in GENDERS:
        raise ValueError(f"unrecognized division {label!r}")
    return parts[0], parts[1]


def read_enrollments(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            division = (row.get("division") or "").strip()
            if not division:
                continue
            raw = (row.get("enrolled") or "").strip()
            try:
                counts[division] = int(raw)
            except ValueError:
                raise ValueError(f"{division}: enrolled={raw!r} is not a number")
    return counts


def build_rows(counts: dict[str, int]) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    notes: list[str] = []
    for division in sorted(counts):
        age_group, gender_word = parse_division(division)
        roster, starters = PLAN[age_group]
        enrolled = counts[division]
        if enrolled <= 0:
            notes.append(f"{division}: 0 enrolled, no teams generated")
            continue
        teams = math.ceil(enrolled / roster)
        per_team = enrolled / teams
        notes.append(f"{division}: {enrolled} enrolled / {roster} roster -> "
                     f"{teams} team(s), ~{per_team:.1f} players each")
        for n in range(1, teams + 1):
            rows.append({
                "season": SEASON,
                # e.g. "10U Boys-01" -- rename to the coach's surname once known
                "name": f"{age_group} {gender_word}-{n:02d}",
                "acct_code": "",
                "gender": GENDERS[gender_word],
                "level": LEVEL,
                "birth_year": "",          # blank: this season is age-group based
                "age_group": age_group,
                "minimum_age": "",
                "coach_first_name": "",    # filled in PlayMetrics at assignment time
                "coach_last_name": "",
                "coach_email": "",
                "coach_mobile": "",
                "num_starting_players": str(starters),
            })
    return rows, notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--enrollments", type=Path, required=True,
                        help="CSV with division,enrolled columns")
    parser.add_argument("--out", type=Path, default=Path("teams.csv"))
    parser.add_argument("--season", default=SEASON)
    args = parser.parse_args(argv)

    counts = read_enrollments(args.enrollments)
    if not counts:
        print("No enrollment rows found.", file=sys.stderr)
        return 2

    rows, notes = build_rows(counts)
    for row in rows:
        row["season"] = args.season

    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    for note in notes:
        print(note)
    print(f"\n{len(rows)} team shells -> {args.out}")
    print("Coach columns left blank on purpose: coaches are attached in "
          "PlayMetrics during team assignment, where a parent volunteer can be "
          "installed as head coach in the same motion as their child is placed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
