#!/usr/bin/env python3
"""Create web-ready image derivatives from the OneDrive originals library."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError


SOURCE_ROOT = Path("assets-original")
OUTPUT_ROOT = Path("public/assets")
STATE_PATH = Path(".image-optimizer-state.json")
SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png"}
MAX_DIMENSION = 1920
# This directory preserves favicon source artwork in OneDrive. It intentionally
# has no matching public/assets output because the favicon lives at public/.
EXCLUDED_SOURCE_DIRECTORIES = {"favicon-source"}


@dataclass
class Totals:
    files: int = 0
    source_bytes: int = 0
    output_bytes: int = 0
    optimized: int = 0
    skipped: int = 0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_state() -> dict[str, dict[str, object]]:
    if not STATE_PATH.exists():
        return {}
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Warning: ignoring unreadable state file: {error}", file=sys.stderr)
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        relative: metadata
        for relative, metadata in data.items()
        if relative.split("/", 1)[0] not in EXCLUDED_SOURCE_DIRECTORIES
    }


def write_state(state: dict[str, dict[str, object]]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=STATE_PATH.parent, delete=False
    ) as temporary:
        json.dump(state, temporary, indent=2, sort_keys=True)
        temporary.write("\n")
        temporary_name = temporary.name
    os.replace(temporary_name, STATE_PATH)


def output_format(path: Path) -> str:
    return "JPEG" if path.suffix.lower() in {".jpg", ".jpeg"} else "PNG"


def encode(source: Path, destination: Path) -> None:
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened)
        image.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

        if output_format(destination) == "JPEG":
            if image.mode not in {"RGB", "L"}:
                background = Image.new("RGB", image.size, "white")
                if image.mode == "RGBA":
                    background.paste(image, mask=image.getchannel("A"))
                else:
                    background.paste(image.convert("RGB"))
                image = background
            image.save(destination, "JPEG", quality=82, optimize=True, progressive=True)
        else:
            image.save(destination, "PNG", optimize=True, compress_level=9)


def process(source: Path, destination: Path) -> int:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as opened:
        corrected = ImageOps.exif_transpose(opened)
        must_reencode = (
            max(corrected.size) > MAX_DIMENSION
            or opened.getexif().get(274, 1) not in {1, None}
        )
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.stem}.", suffix=destination.suffix, dir=destination.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    copied_temporary: Path | None = None
    try:
        encode(source, temporary)
        # Keep the smaller valid representation unless the source needs resizing
        # or EXIF-orientation correction to meet the output contract.
        if temporary.stat().st_size < source.stat().st_size or must_reencode:
            os.replace(temporary, destination)
        else:
            temporary.unlink()
            copy_descriptor, copy_name = tempfile.mkstemp(
                prefix=f".{destination.stem}.", suffix=destination.suffix, dir=destination.parent
            )
            copied_temporary = Path(copy_name)
            with source.open("rb") as input_file, os.fdopen(copy_descriptor, "wb") as output_file:
                for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
                    output_file.write(chunk)
            os.replace(copy_name, destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        if copied_temporary is not None:
            copied_temporary.unlink(missing_ok=True)
        raise
    return destination.stat().st_size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="regenerate every managed image")
    # `pnpm images -- --force` forwards the separator on pnpm 11, while older
    # package-manager versions omit it. Support both documented forms.
    command_arguments = sys.argv[1:]
    if command_arguments[:1] == ["--"]:
        command_arguments = command_arguments[1:]
    args = parser.parse_args(command_arguments)

    if not SOURCE_ROOT.is_dir():
        print(f"Original-image directory is unavailable: {SOURCE_ROOT}", file=sys.stderr)
        return 1

    state = load_state()
    totals = Totals()
    failures: list[str] = []

    for source in sorted(SOURCE_ROOT.rglob("*")):
        if not source.is_file() or source.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        relative = source.relative_to(SOURCE_ROOT).as_posix()
        if relative.split("/", 1)[0] in EXCLUDED_SOURCE_DIRECTORIES:
            continue
        destination = OUTPUT_ROOT / relative
        source_hash = sha256(source)
        totals.files += 1
        totals.source_bytes += source.stat().st_size
        previous = state.get(relative, {})
        if not args.force and destination.is_file() and previous.get("source_sha256") == source_hash:
            totals.skipped += 1
            totals.output_bytes += destination.stat().st_size
            continue

        try:
            output_size = process(source, destination)
        except (OSError, UnidentifiedImageError, ValueError) as error:
            failures.append(f"{source}: {error}")
            continue

        state[relative] = {
            "source_sha256": source_hash,
            "source_bytes": source.stat().st_size,
            "output_bytes": output_size,
        }
        totals.optimized += 1
        totals.output_bytes += output_size
        print(f"Optimized {relative}")

    write_state(state)
    savings = totals.source_bytes - totals.output_bytes
    percentage = savings / totals.source_bytes * 100 if totals.source_bytes else 0
    print(
        f"Managed {totals.files} images: originals {totals.source_bytes:,} bytes, "
        f"outputs {totals.output_bytes:,} bytes, savings {savings:,} bytes ({percentage:.1f}%)."
    )
    print(f"Optimized {totals.optimized}; skipped {totals.skipped} unchanged images.")
    if failures:
        print("Failures:", *failures, sep="\n", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
