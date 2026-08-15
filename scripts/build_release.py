#!/usr/bin/env python3
"""Build and validate the deterministic dbsliceAI sample-data release."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


VERSION = "1.1.0"
FORMAT_VERSION = "1.1"
ROOT_NAME = f"dbslice-ai-sample-data-{VERSION}"
ARCHIVE_NAME = f"{ROOT_NAME}.zip"
MANIFEST_NAME = f"{ROOT_NAME}-manifest.json"
MAX_PAYLOAD_BYTES = 16 * 1024 * 1024
PEXIT_VALUES = (120000, 124000, 128000, 132000, 136000, 140000, 144000, 148000)
EXPECTED_PRESSURE_COUNTS = {
    120000: 9,
    124000: 9,
    128000: 9,
    132000: 9,
    136000: 9,
    140000: 8,
    144000: 5,
    148000: 3,
}
ZIP_TIMESTAMP = (2026, 8, 15, 0, 0, 0)
CURATED_REFERENCES_PATH = "curated_references/papers.json"


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def selected_items(source_root: Path) -> list[dict[str, Any]]:
    metadata = read_json(source_root / "data" / "metaData.json")
    require(isinstance(metadata, dict), "source metadata must be an object")
    items = metadata.get("items")
    require(isinstance(items, list), "source metadata must contain an items array")
    selected = [
        item
        for item in items
        if isinstance(item, dict)
        and item.get("nstat") == 100
        and item.get("pexit") in PEXIT_VALUES
    ]
    item_ids = [item.get("itemId") for item in selected]
    require(len(selected) == 61, f"expected 61 selected items, found {len(selected)}")
    require(
        all(isinstance(item_id, str) and item_id for item_id in item_ids),
        "every selected item must have a non-empty string itemId",
    )
    require(len(set(item_ids)) == len(item_ids), "selected item IDs must be unique")
    require(item_ids[0] == "run_190", f"unexpected first item: {item_ids[0]}")
    require(item_ids[-1] == "run_892", f"unexpected last item: {item_ids[-1]}")
    counts = Counter(item["pexit"] for item in selected)
    require(dict(counts) == EXPECTED_PRESSURE_COUNTS, f"unexpected pexit counts: {dict(counts)}")
    return selected


def release_config() -> dict[str, Any]:
    return {
        "dataset": {
            "title": "Axial Compressor Stator Sample",
            "context": {
                "summary": (
                    "A compact axial compressor stator CFD sample for exploring how "
                    "compound lean and exit pressure affect aerodynamic loss and separation "
                    "at a fixed count of 100 stators."
                ),
                "primaryInputs": ["compound_lean", "pexit"],
                "primaryOutputs": ["Yp", "Yp_hub", "Yp_mid", "Yp_tip", "hub_sep_size"],
                "primaryExtracts": [
                    "Yp-downstream",
                    "stator_exit_line_Yp",
                    "stator_3d_surface",
                ],
            },
        },
        "metaData": {
            "path": "data/metadata/items.json",
            "config": {
                "title": "Axial Compressor Stator Sample",
                "description": (
                    "61 converged cases at 100 stators and exit pressures from "
                    "120 kPa to 148 kPa"
                ),
                "author": "Graham Pullan",
                "release": f"v{VERSION}",
                "datasetFormatVersion": FORMAT_VERSION,
            },
        },
        "curatedReferences": {
            "path": CURATED_REFERENCES_PATH,
        },
        "extracts": [
            {
                "extractId": "Yp-downstream",
                "description": "Yp downstream slice. High Yp means high loss.",
                "type": "image",
                "path": "data/extracts/Yp-downstream/${itemId}.png",
                "format": "png",
                "embedding": {
                    "type": "grid",
                    "source": "file",
                    "path": "data/extracts/Yp-downstream/${itemId}_grid_embed.json",
                    "description": "3x3 grid embedding for the Yp downstream slice.",
                    "settings": {
                        "shape": [3, 3],
                        "regions": [
                            {"index": [0, 0], "name": "Hub Suction-Surface Corner"},
                            {"index": [0, 1], "name": "Hub"},
                            {"index": [0, 2], "name": "Hub Pressure-Surface Corner"},
                            {"index": [1, 0], "name": "Mid Suction-Surface"},
                            {"index": [1, 1], "name": "Mid"},
                            {"index": [1, 2], "name": "Mid Pressure-Surface"},
                            {"index": [2, 0], "name": "Tip Suction-Surface Corner"},
                            {"index": [2, 1], "name": "Tip"},
                            {"index": [2, 2], "name": "Tip Pressure-Surface Corner"},
                        ],
                    },
                },
            },
            {
                "extractId": "stator_exit_line_Yp",
                "description": "Spanwise line of Yp loss coefficient at the stator exit.",
                "type": "line",
                "path": "data/extracts/stator_exit_line_Yp/${itemId}.json",
                "format": "json",
                "xLabel": "Yp",
                "yLabel": "Span fraction",
                "embedding": {
                    "type": "cells",
                    "source": "computed",
                    "method": "line_bins",
                    "description": "Five length-weighted spanwise summaries of the exit Yp line.",
                    "settings": {
                        "monotonicAxis": "y",
                        "bins": 5,
                        "aggregation": "length_weighted",
                    },
                },
                "filter": {"type": "line", "settings": {"lineId": "Yp"}},
            },
            {
                "extractId": "stator_3d_surface",
                "description": (
                    "Stator blades coloured by pressure and an exit cut plane coloured by "
                    "loss coefficient Yp."
                ),
                "type": "glb",
                "path": "data/extracts/stator_3d_surface/${itemId}.glb",
                "format": "glb",
                "render": {
                    "cameraDirection": {"x": -1, "y": 0.5, "z": 0.5},
                    "ambientLightIntensity": 3,
                    "directionalLightIntensity": 1.5,
                },
            },
        ],
    }


def curated_references(repository_root: Path) -> list[dict[str, Any]]:
    references = read_json(repository_root / CURATED_REFERENCES_PATH)
    require(isinstance(references, list), "curated reference manifest must be an array")
    require(len(references) == 1, f"expected one curated reference, found {len(references)}")
    reference = references[0]
    require(isinstance(reference, dict), "curated reference must be an object")
    require(
        reference.get("paperId") == "taylor_miller_2016_competing_3d_mechanisms",
        "unexpected curated reference paperId",
    )
    require(isinstance(reference.get("title"), str) and reference["title"].strip(), "reference title is required")
    parsed_url = urlparse(reference.get("url", ""))
    require(parsed_url.scheme == "https" and parsed_url.netloc, "reference URL must use HTTPS")
    require(isinstance(reference.get("summary"), str) and reference["summary"].strip(), "reference summary is required")
    require(reference.get("contentType") == "text/html", "reference contentType must describe the repository page")
    require("All rights reserved" in reference.get("rights", ""), "reference rights notice is required")
    require("filename" not in reference and "path" not in reference, "the sample must not redistribute the paper")
    return references


def validate_line(path: Path) -> None:
    payload = read_json(path)
    points = payload if isinstance(payload, list) else payload.get("data") if isinstance(payload, dict) else None
    require(isinstance(points, list) and points, f"line payload has no points: {path.name}")
    y_values = []
    for index, point in enumerate(points):
        require(isinstance(point, dict), f"line point {index} is not an object: {path.name}")
        for axis in ("x", "y"):
            value = point.get(axis)
            require(
                not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value),
                f"line point {index}.{axis} is not finite: {path.name}",
            )
        y_values.append(point["y"])
    deltas = [right - left for left, right in zip(y_values, y_values[1:])]
    require(
        not (any(delta > 0 for delta in deltas) and any(delta < 0 for delta in deltas)),
        f"line is not monotonic along y: {path.name}",
    )


def validate_embedding(path: Path) -> None:
    payload = read_json(path)
    require(isinstance(payload, dict), f"embedding must be an object: {path.name}")
    require(payload.get("shape") == [3, 3], f"unexpected embedding shape: {path.name}")
    cells = payload.get("cells")
    require(isinstance(cells, list) and len(cells) == 9, f"expected 9 cells: {path.name}")
    indices = []
    for position, cell in enumerate(cells):
        require(isinstance(cell, dict), f"cell {position} is not an object: {path.name}")
        index = cell.get("index")
        require(
            isinstance(index, list)
            and len(index) == 2
            and all(isinstance(value, int) and 0 <= value < 3 for value in index),
            f"invalid cell index at {position}: {path.name}",
        )
        average = cell.get("avg")
        require(
            not isinstance(average, bool)
            and isinstance(average, (int, float))
            and math.isfinite(average),
            f"invalid cell average at {position}: {path.name}",
        )
        indices.append(tuple(index))
    require(len(set(indices)) == 9, f"embedding cell indices are not unique: {path.name}")


def checked_copy(source: Path, target: Path, kind: str) -> None:
    require(source.is_file(), f"missing source payload: {source}")
    size = source.stat().st_size
    require(size <= MAX_PAYLOAD_BYTES, f"payload exceeds 16 MiB: {source.name} ({size} bytes)")
    if kind == "png":
        require(source.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", f"invalid PNG: {source.name}")
    elif kind == "glb":
        require(source.read_bytes()[:4] == b"glTF", f"invalid GLB: {source.name}")
    elif kind == "line":
        validate_line(source)
    elif kind == "embedding":
        validate_embedding(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def populate_dataset(
    source_root: Path,
    dataset_root: Path,
    items: list[dict[str, Any]],
    references: list[dict[str, Any]],
) -> None:
    write_json(dataset_root / "config" / "config.json", release_config())
    write_json(dataset_root / "data" / "metadata" / "items.json", {"items": items})
    write_json(dataset_root / CURATED_REFERENCES_PATH, references)
    for item in items:
        item_id = item["itemId"]
        copies = (
            (
                source_root / "data" / "extracts" / "stator_exit" / f"{item_id}.png",
                dataset_root / "data" / "extracts" / "Yp-downstream" / f"{item_id}.png",
                "png",
            ),
            (
                source_root / "data" / "extracts" / "stator_exit" / f"{item_id}_grid_embed.json",
                dataset_root / "data" / "extracts" / "Yp-downstream" / f"{item_id}_grid_embed.json",
                "embedding",
            ),
            (
                source_root / "data" / "extracts" / "stator_exit_lines" / f"{item_id}_stator_exit_line_Yp.json",
                dataset_root / "data" / "extracts" / "stator_exit_line_Yp" / f"{item_id}.json",
                "line",
            ),
            (
                source_root / "data" / "extracts" / "stator_3d_surface" / f"{item_id}.glb",
                dataset_root / "data" / "extracts" / "stator_3d_surface" / f"{item_id}.glb",
                "glb",
            ),
        )
        for source, target, kind in copies:
            checked_copy(source, target, kind)


def archive_files(dataset_root: Path) -> list[Path]:
    return sorted(path for path in dataset_root.rglob("*") if path.is_file())


def write_deterministic_zip(dataset_root: Path, archive_path: Path) -> None:
    with zipfile.ZipFile(
        archive_path,
        mode="x",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for source in archive_files(dataset_root):
            relative = source.relative_to(dataset_root.parent).as_posix()
            info = zipfile.ZipInfo(relative, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            with source.open("rb") as handle:
                archive.writestr(info, handle.read(), compresslevel=9)


def build_manifest(
    dataset_root: Path,
    archive_path: Path,
    items: list[dict[str, Any]],
    references: list[dict[str, Any]],
) -> dict[str, Any]:
    files = []
    payload_bytes = 0
    maximum_payload_bytes = 0
    for path in archive_files(dataset_root):
        size = path.stat().st_size
        relative = path.relative_to(dataset_root).as_posix()
        files.append({"path": relative, "bytes": size, "sha256": sha256(path)})
        if relative.startswith("data/extracts/"):
            payload_bytes += size
            maximum_payload_bytes = max(maximum_payload_bytes, size)
    return {
        "release": f"v{VERSION}",
        "datasetFormatVersion": FORMAT_VERSION,
        "licence": "CC BY 4.0",
        "copyright": "Graham Pullan",
        "archive": {
            "fileName": archive_path.name,
            "root": ROOT_NAME,
            "bytes": archive_path.stat().st_size,
            "sha256": sha256(archive_path),
        },
        "selection": {
            "itemCount": len(items),
            "firstItemId": items[0]["itemId"],
            "lastItemId": items[-1]["itemId"],
            "nstat": 100,
            "pexitValuesPa": list(PEXIT_VALUES),
            "pexitItemCounts": {str(key): value for key, value in EXPECTED_PRESSURE_COUNTS.items()},
        },
        "extracts": ["Yp-downstream", "stator_exit_line_Yp", "stator_3d_surface"],
        "curatedReferences": [reference["paperId"] for reference in references],
        "fileCount": len(files),
        "extractPayloadBytes": payload_bytes,
        "maximumPayloadBytes": maximum_payload_bytes,
        "files": files,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dataset", type=Path)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()

    source_root = args.source_dataset.resolve()
    output_root = args.output_directory.resolve()
    repository_root = Path(__file__).resolve().parents[1]
    require((source_root / "config" / "config.json").is_file(), "source dataset is missing config/config.json")
    require(
        not output_root.is_relative_to(repository_root),
        "output directory must be outside the sample-data Git worktree",
    )
    output_root.mkdir(parents=True, exist_ok=True)

    archive_path = output_root / ARCHIVE_NAME
    manifest_path = output_root / MANIFEST_NAME
    checksums_path = output_root / "SHA256SUMS"
    for path in (archive_path, manifest_path, checksums_path):
        require(not path.exists(), f"output already exists: {path}")

    items = selected_items(source_root)
    references = curated_references(repository_root)
    with tempfile.TemporaryDirectory(prefix="dbslice-sample-build-", dir=output_root) as temporary:
        dataset_root = Path(temporary) / ROOT_NAME
        populate_dataset(source_root, dataset_root, items, references)
        write_deterministic_zip(dataset_root, archive_path)
        manifest = build_manifest(dataset_root, archive_path, items, references)
        write_json(manifest_path, manifest)

    checksums_path.write_text(
        f"{sha256(archive_path)}  {archive_path.name}\n"
        f"{sha256(manifest_path)}  {manifest_path.name}\n",
        encoding="utf-8",
    )
    print(f"built {archive_path}")
    print(f"items: {len(items)}")
    print(f"files: {manifest['fileCount']}")
    print(f"extract payload bytes: {manifest['extractPayloadBytes']}")
    print(f"archive sha256: {manifest['archive']['sha256']}")


if __name__ == "__main__":
    main()
