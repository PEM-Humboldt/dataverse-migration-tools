from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import time
import xmltodict
import requests
from src.config import Config
from src.utilitarios.session import api_call    
from src.formato.geonetwork_format import inventory_row
from src.utilitarios.files import write_bytes, write_csv, write_json
from src.utilitarios.logger import logger

config = Config()
PAGE_SIZE = 100

def harvest_server():
    site = api_call("/api/site")
    write_json(site.json(), Path(config.gn_data_dir), "site.json")

    user = api_call("/api/me")
    profile = user.json().get("profile") if user.status_code == 200 and user.content else None
    if profile != "Administrator":
        raise RuntimeError(f"/api/me: the account is not an administrator (profile: {profile}, "
                           f"HTTP {user.status_code}); check GN_USER and GN_PASSWORD")
    
    groups = api_call("/api/groups", withReservedGroup="true")
    write_json(groups.json(), Path(config.gn_data_dir), "groups.json")

def extract_metadata(page):
    """Returns resources in one page of the service."""
    records = page.get("metadata", [])
    return [records] if isinstance(records, dict) else records

def summary_count(page):
    """Total number of records, from the summary of a page requested with buildSummary=true."""
    return int(page["summary"]["@count"])

def fetch_resources_page(start):
    end = start + PAGE_SIZE - 1
    params = {"_content_type": "json", "fast": "index", "from": start, "to": end, "_isTemplate": "n", "buildSummary": "true" if start == 1 else "false"}
    r = api_call("/eng/q", accept="*/*", **params)

    write_bytes(r.content, Path(config.gn_data_dir) / "inventory", f"q_{start:05d}-{end:05d}.json")
    return r.json()

def build_inventory():
    """Creates an inventory with the metadata records (templates excluded), by pages of 100. The first loop returns a summary of the total of records.
    Saves each page as is in /inventory/q_<from>-<to>.json and the full record table in inventory/inventory.csv.
    """
    summary = []
    first = fetch_resources_page(1)
    total = summary_count(first)
    records = extract_metadata(first)

    logger.info(f"The total of records found in Geonetwork is {total}")

    record_files = []
    for start in range(PAGE_SIZE + 1, total + 1, PAGE_SIZE):
        logger.info(f"Retrieving record's metadata from {start} to {start + PAGE_SIZE}")
        records += extract_metadata(fetch_resources_page(start))

    for r in records:
        data, files = inventory_row(r)
        summary.append(data)
        record_files.append(files)
    
    # Extracts all the uniques uuid values
    uuid_len = len({r["uuid"] for r in summary})
    logger.info(f"Found {uuid_len} unique UUIDs")
    if uuid_len != total:
        raise RuntimeError(f"An error occured! {total} records announced, but got {uuid_len} unique UUIDs instead. Please, run the script again.")
    
    summary.sort(key=lambda r: r["uuid"])
    write_csv(summary, Path(config.gn_data_dir) / "inventory", "inventory.csv")
    write_csv(record_files, Path(config.gn_data_dir) / "inventory", "files_inventory.csv")
    
    return summary

def fetch_record_xml(u):
    try:
        record = api_call(f"/api/records/{u}/formatters/xml", accept="application/xml", increasePopularity="false")
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 400:
            logger.warning(f"An error occured while fetching the endpoint formatters/xml. Fetching raw XML for {u}")
            print(f"An error occured but im handling it {e}")
            url_raw = f"/api/records/{u}"
            record = api_call(url_raw, accept="application/xml")
        else:
            raise
    content = record.content.strip()
    if b"MD_Metadata" not in content[:2000] and not content.startswith(b"<?xml"):
        raise ValueError(f"Record {u}: la respuesta no es un documento XML válido")
    
    return record

def fetch_record_attachements(u):
    record = api_call(f"/api/records/{u}/attachments")
    record.raise_for_status()
    try:
        record.json()
    except ValueError as e:
        raise ValueError(f"Record {u}: invalid JSON in attachments response: {e}")
    return record

def fetch_record_sharing(u):
    record = api_call(f"/api/records/{u}/sharing")
    record.raise_for_status()
    try:
        record.json()
    except ValueError as e:
        raise ValueError(f"Record {u}: invalid JSON in sharing response: {e}")
    return record

def harvest_single_uuid(uuid, steps):
    """Fetches and saves metadata XML, a json for file references and a json for resource groups and privileges."""
    uuid_errors = []
    for step_name, fetch_func in steps:
        base_path = Path(config.gn_data_dir) / step_name
        file_path = base_path / f"{uuid}.json"

        if file_path.exists():
            continue

        try:
            r = fetch_func(uuid)
            if step_name == 'xml':
                write_json(xmltodict.parse(r.content), base_path, f"{uuid}.json")
            else:
                write_bytes(r.content, base_path, f"{uuid}.json")
        except (requests.RequestException, ValueError, OSError) as e:
            uuid_errors.append(f"Error en {step_name} para UUID {uuid}: {e}")

    return uuid_errors

def harvest_records(uuids):
    """Runs harvest_single_uuid for all resources available."""
    errors = []

    steps = [
        ("xml", fetch_record_xml),
        ("attachments", fetch_record_attachements),
        ("sharing", fetch_record_sharing),
    ]

    uuids = uuids[:150]
    total=len(uuids)

    start_time = time.perf_counter()
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_uuid = {
            executor.submit(harvest_single_uuid, uuid, steps): uuid
            for uuid in uuids
        }

        completed = 0
        for future in as_completed(future_to_uuid):
            completed += 1
            uuid_errors = future.result()
            if uuid_errors:
                errors.extend(uuid_errors)

            if completed % 25 == 0 or completed == total:
                elapsed = time.perf_counter() - start_time
                logger.info(f"Progreso: {completed}/{total} registros procesados ({len(errors)} errores) - {elapsed:.1f}s transcurridos")

    logger.info(f"Fetching of {total} resources is now finished.")
    return errors

def main():
    try:
        harvest_server()

        rows = build_inventory()
        uuids = [r["uuid"] for r in rows]
        errors = harvest_records(uuids)
        for e in errors:
            logger.error(e)

        logger.info("Harvesting succesfully finished!")
    except Exception as e:
        logger.exception("An error occured while harvesting the Geonetwork server. Aborting.")


if __name__ == "__main__":
    main()