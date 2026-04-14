"""Command line interface for EasyJupyter."""

import argparse
import sys
import os
import time
from EasyJupyter import PROJECT_ROOT, SHADOW_DIR, console, UPDATED_NOTEBOOKS
from EasyJupyter.loader import EasyJupyterLoader
from EasyJupyter.utils import cleanup_cache, sync_all, stop_daemon

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", help="Wipe the cache folder")
    parser.add_argument(
        "--sync", action="store_true", help="Sync all notebooks manually"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Actively watch the daemon's logs and warnings in the foreground",
    )
    parser.add_argument("--stop", action="store_true", help="Stop the background daemon process")
    args = parser.parse_args()

    if args.clean:
        cleanup_cache(PROJECT_ROOT, SHADOW_DIR, console)
    elif args.sync:
        sync_all(PROJECT_ROOT, SHADOW_DIR, console, UPDATED_NOTEBOOKS, EasyJupyterLoader)
    elif args.watch:
        log_path = os.path.join(SHADOW_DIR, "watcher.log")
        if not os.path.exists(log_path):
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
