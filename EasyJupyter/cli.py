"""Command line interface for EasyJupyter."""

import argparse
import sys
from .loader import sync_all, cleanup_cache, print_nb_update_report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", help="Wipe the cache folder")
    parser.add_argument(
        "--sync", action="store_true", help="Sync all notebooks manually"
    )
    args = parser.parse_args()

    if args.clean:
        cleanup_cache()
    elif args.sync:
        sync_all()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
