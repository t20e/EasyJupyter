"""Command line interface for EasyJupyter."""

import argparse
import sys
import os
from pathlib import Path
import time
import importlib.metadata
from easyjupyter import (
    PROJECT_ROOT,
    SHADOW_DIR,
    console,
    UPDATED_NOTEBOOKS,
    start_background_daemon,
)
from easyjupyter.loader import EasyJupyterLoader
from easyjupyter.utils import cleanup_cache, sync_all, stop_daemon


def main():
    parser = argparse.ArgumentParser()
    try:
        __version__ = importlib.metadata.version("easyjupyter")
    except importlib.metadata.PackageNotFoundError:
        __version__ = "unknown"

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show the version and exit",
    )
    parser.add_argument("--clean", action="store_true", help="Wipe the cache folder")
    parser.add_argument("--sync", action="store_true", help="Sync all notebooks.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rebuild all cache files by bypassing the timestamp freshness check.",
    )

    parser.add_argument(
        "--watch",
        action="store_true",
        help="Actively watch the daemon's logs and warnings in the foreground",
    )
    parser.add_argument(
        "--stop", action="store_true", help="Stop the background daemon process"
    )
    args = parser.parse_args()

    if args.force and not args.sync:
        parser.error("--force can only be used with --sync")

    if args.clean:
        cleanup_cache(PROJECT_ROOT, SHADOW_DIR, console)
    elif args.sync:
        sync_all(
            PROJECT_ROOT,
            SHADOW_DIR,
            console,
            UPDATED_NOTEBOOKS,
            EasyJupyterLoader,
            force_sync=args.force,
        )
        start_background_daemon()
        console.print("[bold green]Background watcher daemon started.[/bold green]")
    elif args.watch:
        log_path = SHADOW_DIR / "watcher.log"
        if not log_path.exists():
            print(f"Log file not found at {log_path}")
            return

        print("👀 Watching EasyJupyter daemon activity (Press Ctrl+C to stop)...")
        try:
            with open(log_path, "r") as f:
                f.seek(0, 2)  # Go to the end of the file
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    sys.stdout.write(line)
                    sys.stdout.flush()
        except KeyboardInterrupt:
            print("\nStopped watching logs.")
    elif args.stop:
        stop_daemon(SHADOW_DIR, console)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
