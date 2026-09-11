"""Fill the database `seed.py` serves. One file, no migration step (ADR 0006).

    python seed.py 2026-08-28

The day is required and has no default. `emr.ROSTER`'s five lines are all 28 August 2026,
so a default of *today* would create nothing on every other day and say so only by
printing a zero.
"""
import argparse
import sys
from datetime import date, datetime
from pathlib import Path

# `seed.py` references the database directly; `run.py` no longer exists.
sys.path.insert(0, str(Path(__file__).parent / "src"))

from noor import seed, store

DEFAULT_DB = Path(__file__).resolve().parent / "noor.db"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Noor's demo database.")
    parser.add_argument("day", type=date.fromisoformat, help="the roster day, YYYY-MM-DD")
    args = parser.parse_args()
    conn = store.connect(DEFAULT_DB)
    # A real clock, so the cache age the Visit List states is the age of this run.
    put = seed.build(conn, day=args.day, at=datetime.now())
    conn.close()
    print(f"{put} Visits on {args.day.isoformat()} in {DEFAULT_DB}")
