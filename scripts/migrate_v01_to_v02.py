from __future__ import annotations

import argparse
from pathlib import Path

from app.migration import migrate_v01_to_v02


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default="data/ledger_v01.json")
    parser.add_argument("--dst", default="data/ledger.json")
    parser.add_argument("--anchor", default="anchors/latest.json")
    args = parser.parse_args()

    src = Path(args.src)
    dst = Path(args.dst)
    anchor = Path(args.anchor)

    out_ledger, out_anchor = migrate_v01_to_v02(src, dst, anchor)
    print(f"migrated ledger: {out_ledger}")
    print(f"migrated anchor: {out_anchor}")


if __name__ == "__main__":
    main()
