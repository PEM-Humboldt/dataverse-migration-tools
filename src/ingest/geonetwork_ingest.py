from pathlib import Path
import time
import requests
from src.config import Config
from src.utilitarios.session import api_call    
from src.utilitarios.files import write_bytes

config = Config()
PAGE_SIZE = 100

def harvest_server():
    site = api_call("/api/site")
    write_bytes(site.content, Path(config.gn_origin_url)/"server", "site.json")

    user = api_call("/api/me")
    profile = user.json().get("profile") if user.status_code == 200 and user.content else None
    if profile != "Administrator":
        raise RuntimeError(f"/api/me: the account is not an administrator (profile: {profile}, "
                           f"HTTP {user.status_code}); check GN_USER and GN_PASSWORD")
    
    groups = api_call("/api/groups", withReservedGroup="true")
    write_bytes(groups.content, Path(config.gn_origin_url) / "server", "groups.json")

    return site.json().get("system/platform/version")

def q_records(page):
    """Records of one page of the q service: `metadata` is a list, or a dict when the page has one record."""
    records = page.get("metadata", [])
    return [records] if isinstance(records, dict) else records


def q_count(page):
    """Total number of records, from the summary of a page requested with buildSummary=true."""
    return int(page["summary"]["@count"])

def fetch_resources_page(start):
    end = start + PAGE_SIZE - 1
    params = {"_content_type": "json", "fast": "index", "from": start, "to": end,
                "_isTemplate": "n", "buildSummary": "true" if start == 1 else "false"}
    r = reader.get("/eng/q", accept="*/*", **params)      # as in the prototype
    write_bytes(r.content, run_dir / "inventory" / f"q_{start:05d}-{end:05d}.json")
    return r.json()

def inventory_row(rec):
    """One row of inventory.csv from one record of the q service (flattened index values)."""
    info = rec["geonet:info"]
    user = (rec.get("userinfo") or "").split("|")      # user|surname|name|profile
    return {
        "uuid": info["uuid"],
        "id": info["id"],
        "schema": info["schema"],
        "title": rec.get("defaultTitle", ""),           # `title` is almost always empty
        "type": _as_text(rec.get("type")),
        "is_template": _as_text(rec.get("isTemplate")),
        "is_harvested": _as_text(rec.get("isHarvested")),
        "is_public": info.get("isPublishedToAll", ""),
        "source": info.get("source", ""),
        "owner_id": _as_text(rec.get("owner")),
        "owner_username": user[0],
        "owner_profile": user[3] if len(user) > 3 else "",
        "group_owner": _as_text(rec.get("groupOwner")),
        "published_for_group": _as_text(rec.get("publishedForGroup")),
        "category": _as_text(rec.get("category")),
        "language": _as_text(rec.get("docLocale")),
        "standard_name": _as_text(rec.get("standardName")),
        "valid": _as_text(rec.get("valid")),
        "create_date": info.get("createDate", ""),
        "change_date": info.get("changeDate", ""),
    }

def build_inventory(reader, run_dir):
    """Inventory of today's metadata records (templates excluded), by pages of 100.

    Saves each page as is in run_dir/inventory/q_<from>-<to>.json and the table in
    run_dir/inventory.csv (one row per record, columns INVENTORY_COLUMNS). Always requests
    everything again (7 requests for 659 records): it is the only step that finds new or
    removed records. The first page also asks for the summary, which gives the total.

    Returns the rows of inventory.csv.
    """
    first = fetch_resources_page(1)
    total = q_count(first)
    records = q_records(first)
    for start in range(PAGE_SIZE + 1, total + 1, PAGE_SIZE):
        records += q_records(fetch_resources_page(start))

    rows = [inventory_row(rec) for rec in records]
    if len({r["uuid"] for r in rows}) != total:
        # a record created or deleted while paging shifts the pages: start the run again
        raise RuntimeError(f"q service: {total} records announced, {len(rows)} received "
                           f"({len({r['uuid'] for r in rows})} distinct UUIDs)")
    rows.sort(key=lambda r: r["uuid"])
    write_csv(rows, run_dir / "inventory.csv", fieldnames=INVENTORY_COLUMNS)
    return rows

def main():
    gn_version = harvest_server()
    print("What does gn_version returns?? I dont know! Is it worth saving it?", gn_version)

    rows = build_inventory(reader, run_dir)
    uuids = [r["uuid"] for r in rows]


if __name__ == "__main__":
    main()