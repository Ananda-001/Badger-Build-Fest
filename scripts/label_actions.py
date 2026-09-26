"""Create or validate an independent, task-level adjudication worksheet."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assay_engine.policy import label_template, validate_labels


def load(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--judgments", type=Path, action="append")
    ap.add_argument("--config", action="append", default=[])
    ap.add_argument("--out", type=Path)
    ap.add_argument("--validate", type=Path)
    a = ap.parse_args()
    if a.validate:
        labels = load(a.validate)
        validate_labels(labels)
        print(json.dumps({"labels": len(labels), "adjudicated": sum(r.get("correct") is not None for r in labels),
                          "unknown": sum(r.get("correct") is None for r in labels)}, indent=2))
        return
    if not a.judgments or not a.config or not a.out:
        ap.error("Template mode requires --judgments, one or more --config values, and --out")
    rows = [row for path in a.judgments for row in load(path)]
    labels = []
    seen = set()
    for config_id in a.config:
        for label in label_template(rows, config_id):
            if label["action_id"] not in seen:
                seen.add(label["action_id"])
                labels.append(label)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("x", encoding="utf-8") as stream:
        for label in labels:
            stream.write(json.dumps(label, ensure_ascii=False) + "\n")
    print(json.dumps({"labels": len(labels), "out": str(a.out), "model_calls": 0}, indent=2))


if __name__ == "__main__":
    main()
