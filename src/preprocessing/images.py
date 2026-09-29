"""Image preprocessing utilities."""

from __future__ import annotations

from pathlib import Path


def list_image_files(image_dir: str | Path):
    image_dir = Path(image_dir)
    return sorted(str(path) for path in image_dir.glob('*') if path.is_file())
