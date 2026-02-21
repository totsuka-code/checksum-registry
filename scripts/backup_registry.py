from __future__ import annotations

from pathlib import Path

from app.backup_restore import perform_backup


def main() -> None:
    out = perform_backup(Path("backups"))
    print(f"backup created: {out}")


if __name__ == "__main__":
    main()
