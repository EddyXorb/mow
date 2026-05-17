#!/usr/bin/env python3
import argparse
from pathlib import Path


def compare_folders(folder1: Path, folder2: Path, ext1: str, ext2: str) -> None:
    ext1 = ext1.lstrip(".").lower()
    ext2 = ext2.lstrip(".").lower()

    source_files = {f.stem.lower() for f in folder1.iterdir() if f.suffix.lower() == f".{ext1}"}
    target_files = {f.stem.lower() for f in folder2.iterdir() if f.suffix.lower() == f".{ext2}"}

    missing = source_files - target_files
    extra = target_files - source_files

    if not missing and not extra:
        print(f"All {len(source_files)} .{ext1} files have a corresponding .{ext2} file.")
        return

    if missing:
        print(f"Missing .{ext2} files for {len(missing)} .{ext1} file(s):")
        # for name in sorted(missing):
        #     print(f"  {name}.{ext1}")

    if extra:
        print(f"\nExtra .{ext2} files with no corresponding .{ext1} file ({len(extra)}):")
        # for name in sorted(extra):
        #     print(f"  {name}.{ext2}")


def main():
    parser = argparse.ArgumentParser(
        description="Check that every file with one extension in folder1 has a counterpart with another extension in folder2."
    )
    parser.add_argument("folder1", type=Path, help="Source folder")
    parser.add_argument("folder2", type=Path, help="Target folder")
    parser.add_argument("--ext1", default="ORF", help="Extension to look for in folder1 (default: ORF)")
    parser.add_argument("--ext2", default="dng", help="Extension to look for in folder2 (default: dng)")
    args = parser.parse_args()

    for folder in (args.folder1, args.folder2):
        if not folder.is_dir():
            parser.error(f"Not a directory: {folder}")

    compare_folders(args.folder1, args.folder2, args.ext1, args.ext2)


if __name__ == "__main__":
    main()
