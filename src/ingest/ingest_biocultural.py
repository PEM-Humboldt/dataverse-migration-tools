"""Harvest of the Biocultural platform metadata (Dataverse 6.6) to one folder per run.

Steps (those of testBiocultural/01_inventory.qmd and 02_harvest.qmd):
1. server: Dataverse version and metadata block definitions;
2. collections from :root, recursively, and inventory of the datasets;
3. all versions of each dataset, with the description of their files;
4. summary (the errors are listed; running again requests only what is missing).

Data files are not downloaded: their description comes with the versions (step 3).
The token must be a superuser's (see env-template).

Usage:  python -m src.ingest.ingest_biocultural [--run-dir data_raw/biocultural/YYYY-MM-DD] [--delay 1]
"""
import argparse
import datetime
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from src.ingest.dataverse_reader import DataverseReader
from src.utilitarios.files import pid_to_stem, write_csv, write_json


def harvest_server(reader, run_dir):
    """Dataverse version and metadata block definitions

    The list of blocks is requested to discover their names ;
    only the definitions are saved.

    Returns the Dataverse version.
    """
    version = reader.get("/api/info/version")
    write_json(version, run_dir / "server" / "version.json")
    for block in reader.get_data("/api/metadatablocks"):    # block names, not saved
        write_json(reader.get(f"/api/metadatablocks/{block['name']}"),
                   run_dir / "server" / "metadatablocks" / f"{block['name']}.json")
    return version["data"].get("version")


def dataset_pid(item):
    """Persistent identifier of a `dataset` item of /contents (protocol, authority, separator, identifier).

    Built from the item's fields, not from a fixed prefix: some datasets have another
    prefix (doi:10.5072/FK2/MH9E0K, a DataCite test DOI).
    """
    return f"{item['protocol']}:{item['authority']}{item.get('separator', '/')}{item['identifier']}"


def build_inventory(reader, run_dir):
    """Walk the collections from :root and write the inventory of today's datasets.

    Saves the responses in run_dir/collections/ and the list in run_dir/inventory.csv
    (persistent_id, dataset_id, collection). Always requests everything again (about
    5 requests): it is the only step that finds new datasets, drafts or collections.
    """
    root = reader.get_data("/api/dataverses/:root")
    queue, datasets = [root["id"]], []
    while queue:                                      # collections form a tree: no cycles
        coll_id = queue.pop(0)
        coll = reader.get(f"/api/dataverses/{coll_id}")
        write_json(coll, run_dir / "collections" / f"{coll_id}.json")
        contents = reader.get(f"/api/dataverses/{coll_id}/contents")
        write_json(contents, run_dir / "collections" / f"{coll_id}_contents.json")
        for item in contents["data"]:
            if item["type"] == "dataverse":
                queue.append(item["id"])              # sub-collection: walked later
            elif item["type"] == "dataset":
                datasets.append({"persistent_id": dataset_pid(item), "dataset_id": item["id"],
                                 "collection": coll["data"]["alias"]})
    datasets.sort(key=lambda d: d["dataset_id"])
    write_csv(datasets, run_dir / "inventory.csv")
    return datasets


def harvest_versions(reader, datasets, run_dir):
    """All versions of each dataset (drafts and deaccessioned included), with their files.

    One request per dataset, by its internal identifier (works also for drafts whose DOI
    was never registered). Skips what is already saved in this run; an error is recorded
    and the dataset is left without a file, to be requested in the next run.
    Returns the list of errors.
    """
    errors = []
    for ds in datasets:
        path = run_dir / "datasets" / f"{pid_to_stem(ds['persistent_id'])}.json"
        if path.exists():
            continue
        try:
            response = reader.get(f"/api/datasets/{ds['dataset_id']}/versions",
                                  includeDeaccessioned="true")
        except (requests.RequestException, RuntimeError) as e:
            errors.append(f"{ds['persistent_id']} ({ds['dataset_id']}): {e}")
            continue
        write_json(response, path)
    return errors


def harvest(reader, run_dir):
    """Full harvest in `run_dir`: server, today's inventory and versions. Returns the list of errors."""
    run_dir = Path(run_dir)
    dataverse_version = harvest_server(reader, run_dir)
    datasets = build_inventory(reader, run_dir)
    errors = harvest_versions(reader, datasets, run_dir)
    print(f"Dataverse {dataverse_version} - datasets: {len(datasets)}"
          f" - requests: {reader.n_requests} - errors: {len(errors)}")
    for e in errors:
        print("  ", e)
    return errors


def main():
    parser = argparse.ArgumentParser(description="Harvest of the Biocultural platform metadata")
    parser.add_argument("--run-dir", type=Path,
                        default=Path("data_raw/biocultural") / datetime.date.today().isoformat(),
                        help="folder of the run (default: data_raw/biocultural/<today's date>)")
    parser.add_argument("--delay", type=float, default=1.0, help="pause between requests (seconds)")
    args = parser.parse_args()
    load_dotenv()
    reader = DataverseReader(os.environ["BIO_DV_URL"], os.environ["BIO_DV_API_TOKEN"], delay=args.delay)
    errors = harvest(reader, args.run_dir)
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
