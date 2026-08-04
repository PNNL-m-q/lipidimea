"""
lipidimea.review.__main__
=========================

Console-script entry point. Installed as `lipidimea-review`:

    lipidimea-review                    # opens app, no DB loaded
    lipidimea-review path/to.db         # opens with DB pre-loaded
    lipidimea-review --help

Also runnable as a module:

    python -m lipidimea.review [path/to.db]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .app import ReviewApp


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="lipidimea-review",
        description=(
            "Interactive review GUI for lipidimea results databases. "
            "Step through DIA feature groups, inspect MS1/XIC/ATD/MS2 "
            "diagnostic plots, mark bad features/groups/annotations for "
            "deletion, then commit deletions or export the retained set "
            "to CSV."
        ),
    )
    parser.add_argument(
        "db_path",
        nargs="?",
        type=Path,
        default=None,
        help="optional path to a results database to open on startup",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.db_path is not None and not args.db_path.exists():
        print(
            f"error: database file does not exist: {args.db_path}",
            file=sys.stderr,
        )
        return 2

    app = ReviewApp(db_path=args.db_path)
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
    