"""Harvest of the GeoNetwork I2D catalogue (GeoNetwork 3.2.2) to one folder per run.

Steps :
1. server: site information, check that the account is an administrator, user groups;
2. inventory of today's metadata records (q service, pages of 100; templates excluded);
3. for each record: ISO 19139 XML, attachment list, privileges;
4. summary (the errors are listed; running again requests only what is missing).

No attachment is downloaded, neither the data files (185 GB) nor the preview images
(gmd:graphicOverview): their list comes with step 3, and they are fetched together later.
Nor are the related records (/api/records/<uuid>/related): all the relations are in the XML
(parentIdentifier, srv:operatesOn, aggregationInfo, lineage sources) and are read offline.

Usage:  python -m src.ingest.geonetwork_harvest [--run-dir data_raw/geonetwork/YYYY-MM-DD] [--delay 1]
"""
import argparse
import datetime
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from src.formato.geonetwork_source import INVENTORY_COLUMNS, inventory_row, q_count, q_records
from src.ingest.geonetwork_reader import GeoNetworkReader
from src.utilitarios.files import write_bytes, write_csv

PAGE_SIZE = 100


def harvest_server(reader, run_dir):
    """Site information and user groups (3 requests); stops if the account is not an administrator.

    /api/me is checked but not saved (it holds the account's personal data). Without an
    administrator account the inventory silently misses the private records (54 on 2026-10-01),
    so the harvest stops here instead.

    Returns the GeoNetwork version.
    """
    site = reader.get("/api/site")
    write_bytes(site.content, run_dir / "server" / "site.json")
    me = reader.get("/api/me")
    profile = me.json().get("profile") if me.status_code == 200 and me.content else None
    if profile != "Administrator":
        raise RuntimeError(f"/api/me: the account is not an administrator (profile: {profile}, "
                           f"HTTP {me.status_code}); check GN_USER and GN_PASSWORD")
    groups = reader.get("/api/groups", withReservedGroup="true")
    write_bytes(groups.content, run_dir / "server" / "groups.json")
    return site.json().get("system/platform/version")


def build_inventory(reader, run_dir):
    """Inventory of today's metadata records (templates excluded), by pages of 100.

    Saves each page as is in run_dir/inventory/q_<from>-<to>.json and the table in
    run_dir/inventory.csv (one row per record, columns INVENTORY_COLUMNS). Always requests
    everything again (7 requests for 659 records): it is the only step that finds new or
    removed records. The first page also asks for the summary, which gives the total.

    Returns the rows of inventory.csv.
    """
    def page(start):
        end = start + PAGE_SIZE - 1
        params = {"_content_type": "json", "fast": "index", "from": start, "to": end,
                  "_isTemplate": "n", "buildSummary": "true" if start == 1 else "false"}
        r = reader.get("/eng/q", accept="*/*", **params)      # as in the prototype
        write_bytes(r.content, run_dir / "inventory" / f"q_{start:05d}-{end:05d}.json")
        return r.json()

    first = page(1)
    total = q_count(first)
    records = q_records(first)
    for start in range(PAGE_SIZE + 1, total + 1, PAGE_SIZE):
        records += q_records(page(start))
    rows = [inventory_row(rec) for rec in records]
    if len({r["uuid"] for r in rows}) != total:
        # a record created or deleted while paging shifts the pages: start the run again
        raise RuntimeError(f"q service: {total} records announced, {len(rows)} received "
                           f"({len({r['uuid'] for r in rows})} distinct UUIDs)")
    rows.sort(key=lambda r: r["uuid"])
    write_csv(rows, run_dir / "inventory.csv", fieldnames=INVENTORY_COLUMNS)
    return rows


def _check_xml(r):
    if b"MD_Metadata" not in r.content[:2000]:
        raise ValueError("the response is not an ISO 19139 record (gmd:MD_Metadata)")


def _check_json(r):
    json.loads(r.content)       # an empty or cut response raises ValueError


# step -> (file suffix, request, check of the response)
RECORD_STEPS = {
    # increasePopularity=false: do not count the download as a view of the record (the
    # parameter defaults to true: MetadataApi.java of GeoNetwork 3.2.2, checked on 2026-10-21)
    "xml": (".xml", lambda reader, u: reader.get(f"/api/records/{u}/formatters/xml",
                                                 accept="application/xml",
                                                 increasePopularity="false"), _check_xml),
    "attachments": (".json", lambda reader, u: reader.get(f"/api/records/{u}/attachments"), _check_json),
    "sharing": (".json", lambda reader, u: reader.get(f"/api/records/{u}/sharing"), _check_json),
}


def harvest_records(reader, uuids, run_dir):
    """XML, attachment list and privileges of each record (3 requests per record).

    Each response is saved as is in run_dir/<step>/<uuid>.<xml|json>. Skips what is already
    saved in this run; an error is recorded and the file is not written, to be requested in
    the next run. Returns the list of errors.
    """
    errors = []
    for i, uuid in enumerate(uuids, start=1):
        for step, (suffix, request, check) in RECORD_STEPS.items():
            path = run_dir / step / f"{uuid}{suffix}"
            if path.exists():
                continue
            try:
                r = request(reader, uuid)
                check(r)
            except (requests.RequestException, ValueError) as e:
                errors.append(f"{step} {uuid}: {e}")
                continue
            write_bytes(r.content, path)
        if i % 50 == 0:
            print(f"  {i}/{len(uuids)} records - {len(errors)} errors")
    return errors


def harvest(reader, run_dir):
    """Full harvest in `run_dir`: server, today's inventory and records. Returns the list of errors."""
    run_dir = Path(run_dir)
    gn_version = harvest_server(reader, run_dir)
    rows = build_inventory(reader, run_dir)
    uuids = [r["uuid"] for r in rows]
    print(f"GeoNetwork {gn_version} - records: {len(rows)}")
    errors = harvest_records(reader, uuids, run_dir)
    print(f"requests: {reader.n_requests} - errors: {len(errors)}")
    for e in errors:
        print("  ", e)
    return errors


def main():
    parser = argparse.ArgumentParser(description="Harvest of the GeoNetwork I2D catalogue")
    parser.add_argument("--run-dir", type=Path,
                        default=Path("data_raw/geonetwork") / datetime.date.today().isoformat(),
                        help="folder of the run (default: data_raw/geonetwork/<today's date>)")
    parser.add_argument("--delay", type=float, default=1.0, help="pause between requests (seconds)")
    args = parser.parse_args()
    load_dotenv()
    reader = GeoNetworkReader(os.environ["GN_URL"], os.environ["GN_USER"], os.environ["GN_PASSWORD"],
                              delay=args.delay)
    errors = harvest(reader, args.run_dir)
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
