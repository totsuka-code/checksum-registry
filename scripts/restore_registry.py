from __future__ import annotations

import argparse
from pathlib import Path

from app.backup_restore import restore_backup


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("backup_dir")
    parser.add_argument("--restore-public-key", action="store_true")
    args = parser.parse_args()

    restore_backup(Path(args.backup_dir), restore_public_key=args.restore_public_key)
    print("restore completed")


if __name__ == "__main__":
    main()
