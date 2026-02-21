from __future__ import annotations

import argparse
import time
from pathlib import Path

from app.hashing import sha256_file_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        raise FileNotFoundError(target)

    start = time.perf_counter()
    digest, size = sha256_file_path(str(target))
    elapsed = time.perf_counter() - start
    mb = size / (1024 * 1024)
    speed = mb / elapsed if elapsed > 0 else 0.0

    print(f"file={target}")
    print(f"size_bytes={size}")
    print(f"sha256={digest}")
    print(f"elapsed_sec={elapsed:.4f}")
    print(f"throughput_mib_per_sec={speed:.2f}")


if __name__ == "__main__":
    main()
