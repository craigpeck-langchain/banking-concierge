"""Export / restore the Engine-generated dataset to/from a JSON file.

Usage:
    # one-time after Engine creates the dataset — dumps to evals/engine_dataset.json
    uv run python evals/engine_dataset.py export

    # after wiping LangSmith for a demo rehearsal — recreates from the JSON
    uv run python evals/engine_dataset.py restore
    uv run python evals/engine_dataset.py restore --reset    # overwrite if exists

The JSON file is meant to be committed to the repo so the
Engine-generated assertions survive deletions and produce a
reproducible baseline for demo practice. If Engine creates a fresh
dataset under the same name, you can either accept it (Engine usually
produces equivalent assertions) or restore from the snapshot.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

load_dotenv(override=True)

DEFAULT_DATASET_NAME = "banking-concierge-hallucinations"
SNAPSHOT_PATH = Path(__file__).resolve().parent / "engine_dataset.json"


def export_dataset(name: str, path: Path) -> None:
    client = Client()
    ds = client.read_dataset(dataset_name=name)
    examples = list(client.list_examples(dataset_id=ds.id))

    payload = {
        "name": ds.name,
        "description": ds.description or "",
        "examples": [
            {
                "inputs": ex.inputs,
                "outputs": ex.outputs,
                "metadata": ex.metadata or {},
            }
            for ex in examples
        ],
    }

    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Exported {len(examples)} examples from {ds.name!r} to {path}")


def restore_dataset(path: Path, reset: bool) -> None:
    if not path.is_file():
        raise SystemExit(
            f"Snapshot not found at {path}. Run `engine_dataset.py export` first."
        )

    payload = json.loads(path.read_text(encoding="utf-8"))
    name = payload["name"]
    description = payload.get("description") or ""
    examples = payload.get("examples", [])

    client = Client()
    existing = list(client.list_datasets(dataset_name=name))
    if existing:
        if not reset:
            print(
                f"Dataset {name!r} already exists in LangSmith. "
                "Pass --reset to delete and recreate it."
            )
            return
        print(f"Deleting existing dataset {name!r}...")
        client.delete_dataset(dataset_name=name)

    ds = client.create_dataset(dataset_name=name, description=description)
    print(f"Created dataset {ds.name} ({ds.id})")

    if not examples:
        print("Snapshot has no examples; dataset created empty.")
        return

    client.create_examples(
        dataset_id=ds.id,
        examples=[
            {
                "inputs": ex.get("inputs", {}),
                "outputs": ex.get("outputs", {}),
                "metadata": ex.get("metadata", {}) or {},
            }
            for ex in examples
        ],
    )
    print(f"Restored {len(examples)} examples.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=("export", "restore"),
        help="export: pull from LangSmith into the snapshot. restore: push snapshot back.",
    )
    parser.add_argument(
        "--name",
        default=DEFAULT_DATASET_NAME,
        help=f"Dataset name in LangSmith (default: {DEFAULT_DATASET_NAME!r}).",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=SNAPSHOT_PATH,
        help=f"Snapshot file path (default: {SNAPSHOT_PATH}).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="(restore only) Delete and recreate the dataset if it already exists.",
    )
    args = parser.parse_args()

    if args.mode == "export":
        if args.reset:
            print("--reset is ignored in export mode.", file=sys.stderr)
        export_dataset(args.name, args.path)
    else:
        restore_dataset(args.path, args.reset)


if __name__ == "__main__":
    main()
