"""Stage everything the Databricks App needs into app/_bundle/ (app.py at the root, as app.yaml expects).

    python app/make_bundle.py              # code + data files
    python app/make_bundle.py --no-data    # code only (the app reads data from ASSAY_DATA_VOLUME instead)

Databricks Apps rejects any source file over 10 MB, so big .jsonl files are gzipped, and split into
<name>.partNN.jsonl.gz shards if they are still too big. app_data.load_jsonl reads all of these forms.
Sample data (data/sample/) is never bundled.
"""
from __future__ import annotations

import argparse
import gzip
import shutil
from pathlib import Path

APP = Path(__file__).resolve().parent
ROOT = APP.parent
OUT = APP / "_bundle"
LIMIT = 9_500_000  # bytes; stay under the 10 MB per-file cap
APP_FILES = ("app.py", "app_data.py", "sample_data.py", "app.yaml", "requirements.txt")
PACKAGES = ("assay_engine", "assay_triage")
DATA_FILES = ("tickets.jsonl", "judgments.jsonl", "candidates.jsonl", "feedback.jsonl", "model_compare.json")


def _copy_data(src: Path, dst_dir: Path) -> list[str]:
    if src.stat().st_size <= LIMIT:
        shutil.copy2(src, dst_dir / src.name)
        return [src.name]
    gz = dst_dir / (src.name + ".gz")
    with src.open("rb") as f, gzip.open(gz, "wb") as g:
        shutil.copyfileobj(f, g)
    if gz.stat().st_size <= LIMIT:
        return [gz.name]
    gz.unlink()
    names, part, buf, size = [], 0, [], 0

    def flush():
        nonlocal part, buf, size
        name = f"{src.stem}.part{part:02d}.jsonl.gz"
        with gzip.open(dst_dir / name, "wb") as g:
            g.writelines(buf)
        names.append(name)
        part, buf, size = part + 1, [], 0

    with src.open("rb") as f:
        for line in f:
            buf.append(line)
            size += len(line)
            if size >= LIMIT * 3:  # jsonl text gzips well over 3x
                flush()
    if buf:
        flush()
    return names


def build(out: Path = OUT, data: bool = True) -> list[str]:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    written = []
    for name in APP_FILES:
        shutil.copy2(APP / name, out / name)
        written.append(name)
    for pkg in PACKAGES:
        src = ROOT / pkg
        if src.exists():
            shutil.copytree(src, out / pkg, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            written.append(pkg + "/")
    if data:
        (out / "data").mkdir()
        for name in DATA_FILES:
            src = ROOT / "data" / name
            if src.exists():
                written += ["data/" + n for n in _copy_data(src, out / "data")]
    too_big = [p for p in out.rglob("*") if p.is_file() and p.stat().st_size > 10_000_000]
    if too_big:
        raise SystemExit(f"still over 10 MB: {too_big}")
    return written


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-data", action="store_true", help="bundle code only; data comes from ASSAY_DATA_VOLUME")
    a = ap.parse_args()
    for w in build(data=not a.no_data):
        print("  ", w)
    print(f"bundle ready: {OUT}")
