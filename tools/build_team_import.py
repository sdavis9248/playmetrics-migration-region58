#!/usr/bin/env python3
"""Generate a PlayMetrics Import Teams CSV for AYSO Region 58.

Reads `packages.json` -- the same feed the Region 58 Portal uses -- so team
counts come from live "Active Registrations X of Y" data rather than a
hand-maintained spreadsheet. The Packages tab is the *only* source for max
spots; they appear in no export CSV.

    # from the producer's output directory
    python build_team_import.py --packages ../../AYSORegionAutomation/data/playmetrics/packages.json

    # or straight from the bucket
    gsutil cp gs://region58-portal-data/packages.json .
    python build_team_import.py --packages packages.json --out teams.csv

Division sizing mirrors region58-portal's DIVISION_CONFIG (data_service.py),
which is the source of truth -- if roster sizes change there, update them here.
The team-count arithmetic deliberately does NOT match the portal's; see
team_count() for why.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

# PlayMetrics sample-teams template, in order. Never reorder or drop a header --
# the import errors out on a missing header even when the value below it is blank.
COLUMNS = [
    "season", "name", "acct_code", "gender", "level", "birth_year", "age_group",
    "minimum_age", "coach_first_name", "coach_last_name", "coach_email",
    "coach_mobile", "num_starting_players",
]

SEASON = "Fall 2026"   # must match the PlayMetrics Season name exactly
LEVEL = "Core"         # CONFIRM: sample template showed Classic / Academy

# Mirrors region58-portal data_service.DIVISION_CONFIG. on_field is what the
# import calls num_starting_players -- players at kickoff, NOT roster size.
DIVISION_CONFIG = {
    "05U Schoolyard Coed": {"roster_size":  0, "roster_min":  0, "on_field":  0},
    "06UB Boys":           {"roster_size":  6, "roster_min":  5, "on_field":  4},
    "06UG Girls":          {"roster_size":  6, "roster_min":  5, "on_field":  4},
    "07UB Boys":           {"roster_size":  7, "roster_min":  6, "on_field":  4},
    "07UG Girls":          {"roster_size":  7, "roster_min":  6, "on_field":  4},
    "08UB Boys":           {"roster_size":  7, "roster_min":  6, "on_field":  5},
    "08UG Girls":          {"roster_size":  7, "roster_min":  6, "on_field":  5},
    "10UB Boys":           {"roster_size":  9, "roster_min":  8, "on_field":  7},
    "10UG Girls":          {"roster_size":  9, "roster_min":  8, "on_field":  7},
    "12UB Boys":           {"roster_size": 12, "roster_min": 10, "on_field":  9},
    "12UG Girls":          {"roster_size": 12, "roster_min": 10, "on_field":  9},
    "14UB Boys":           {"roster_size": 14, "roster_min": 12, "on_field": 11},
    "14UG Girls":          {"roster_size": 14, "roster_min": 12, "on_field": 11},
    "16UB Boys":           {"roster_size": 14, "roster_min": 12, "on_field": 11},
    "16UG Girls":          {"roster_size": 14, "roster_min": 12, "on_field": 11},
    "19UB Boys":           {"roster_size": 22, "roster_min": 12, "on_field": 11},
    "19UG Girls":          {"roster_size": 22, "roster_min": 12, "on_field": 11},
}

# Gendered division codes must be matched whole. Substring-matching the first
# three chars merges Boys and Girls and silently inflates every count.
DIV_RE = re.compile(r"^(\d{2})U([BG])\s", re.I)


def clean_division(name: str) -> str:
    """PlayMetrics package names carry a date-range suffix; drop it.

    '10UB Boys - August 1, 2016 - July 31, 2018' -> '10UB Boys'
    """
    return name.split(" - ", 1)[0].strip()


def team_count(active: int, maximum: int, waitlist: int, cfg: dict) -> int:
    """How many team shells this division needs.

    DELIBERATELY DIFFERENT from region58-portal's current_teams, which floors:
    `int(capped / roster)`. That is right for the portal, where the number
    answers "how many *full* teams does this enrollment support" -- a fullness
    metric. It is wrong for creating shells, because flooring leaves players
    with nowhere to sit: 84 players at roster 9 floors to 9 teams of 9.3, and
    40 at roster 22 floors to a single team of 40. Both exceed the cap.

    Everyone Plays means every registered player needs a seat, so we round up.
    The roster_min guard is kept from the portal: a division just under one
    full roster still forms its single team.
    """
    roster = cfg["roster_size"]
    if roster <= 0:
        return 0
    if active < cfg["roster_min"]:
        return 0
    return math.ceil(active / roster)


def load_packages(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data.get("packages", [])


def build_rows(packages: list[dict], season: str) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    notes: list[str] = []
    for pkg in packages:
        name = clean_division(pkg.get("name", ""))
        cfg = DIVISION_CONFIG.get(name)
        if not cfg:
            # Fee/admin packages ('Additional Fees') have no gender token.
            if DIV_RE.match(name):
                notes.append(f"SKIPPED unknown division {name!r} -- add it to DIVISION_CONFIG")
            continue
        if cfg["roster_size"] == 0:
            notes.append(f"{name}: non-team program, no shells generated")
            continue

        active = int(pkg.get("active_registrations") or 0)
        maximum = int(pkg.get("max_spots") or 0)
        waitlist = int(pkg.get("waitlist") or pkg.get("waitlist_count") or 0)
        teams = team_count(active, maximum, waitlist, cfg)
        if teams <= 0:
            notes.append(f"{name}: {active} enrolled, below one roster -- no teams yet")
            continue

        notes.append(f"{name}: {active}/{maximum} enrolled (+{waitlist} wait) "
                     f"/ {cfg['roster_size']} roster -> {teams} team(s), "
                     f"~{active/teams:.1f} players each")

        gender = "M" if name[3].upper() == "B" else "F"
        age_group = f"{name[:3]}"          # '10U'
        for n in range(1, teams + 1):
            rows.append({
                "season": season,
                "name": f"{name}-{n:02d}",   # '10UB Boys-01'; renamed to coach surname later
                "acct_code": "",
                "gender": gender,
                "level": LEVEL,
                "birth_year": "",            # blank: this season is age-group based
                "age_group": age_group,
                "minimum_age": "",
                "coach_first_name": "",      # coaches attach in PlayMetrics, and are
                "coach_last_name": "",       # emailed the instant they are assigned
                "coach_email": "",
                "coach_mobile": "",
                "num_starting_players": str(cfg["on_field"]),
            })
    return rows, notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--packages", type=Path, required=True,
                        help="packages.json from AYSORegionAutomation or the GCS bucket")
    parser.add_argument("--out", type=Path, default=Path("teams.csv"))
    parser.add_argument("--season", default=SEASON)
    args = parser.parse_args(argv)

    packages = load_packages(args.packages)
    if not packages:
        print("No packages found in that file.", file=sys.stderr)
        return 2

    rows, notes = build_rows(packages, args.season)
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    for note in notes:
        print(note)
    print(f"\n{len(rows)} team shells -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
