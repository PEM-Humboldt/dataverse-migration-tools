"""Reading and writing files: JSON, CSV, and persistent identifiers as file names.

"""
import csv
import io
import json
import os
from pathlib import Path


def read_json(path):
    """Read a UTF-8 JSON file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(obj, path):
    """Write `obj` to a UTF-8 JSON file (accents unescaped, indent of 1), atomically.

    Writes to `<name>.part` first and renames it at the end: after an interruption
    the file is either complete or absent, so a step that skips what is already saved
    can trust whatever it finds.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def write_bytes(content, path):
    """Write `content` (bytes) to `path` unchanged, atomically (`<name>.part`, then renamed).

    For responses saved exactly as the source gave them (XML, JSON not re-encoded).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    tmp.write_bytes(content)
    os.replace(tmp, path)


def read_csv(path):
    """Read a UTF-8 CSV file with a header row; return a list of dictionaries."""
    return list(csv.DictReader(io.StringIO(Path(path).read_text(encoding="utf-8"))))


def write_csv(rows, path, fieldnames=None):
    """Write a list of dictionaries to a UTF-8 CSV file (columns: `fieldnames`, or the keys of the first row)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = fieldnames or (list(rows[0]) if rows else [])
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(buf.getvalue(), encoding="utf-8")


def pid_to_stem(pid):
    """File name (without extension) for a persistent identifier: ":" and "/" become "_".

    doi:10.21068/NMNUPI -> doi_10.21068_NMNUPI
    """
    return pid.replace(":", "_").replace("/", "_")

