from pathlib import Path
from typing import Iterable


def iter_files(root: str | Path, allowed_ext: Iterable[str] = (".txt", ".md", ".pdf")):
    root = Path(root)
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in allowed_ext:
            yield path
