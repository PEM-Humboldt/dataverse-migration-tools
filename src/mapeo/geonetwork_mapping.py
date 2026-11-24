"""Mapping of the GeoNetwork harvest to Dataverse version records.

Reads the harvest of src/ingest/geonetwork_ingest.py (GN_DATA_DIR) and the I2D inventory (INVENTORY_PATH),
applies the crosswalk with the hand-edited tables of src/mapeo/geonetwork/tablas/ (not in the repository:
see tablas/README.md), checks the fields of every record against
the block definitions (<block>.tsv in TSV_FILES_PATH, read by load_dv_schemas()) and writes, in GN_DATA_DIR:

- METADATA_DIR/<uuid>-1.0.json: the version record of each migrated record,
  {"metadataLanguage", "datasetVersion", "inventory_data"}, as for Biocultural;
- load_plan.csv: one row per version record: publish after the load or keep as a draft, access type, licence
  (and, with --with-files, the number of files, the restricted files and their folder);
- version_dates.csv: the original dates of each version, for the SQL script run after the load;
- mapping_problems.json: the records whose fields do not pass the checks (they get no version record);
- files_to_download.csv, only with --with-files: the GeoNetwork attachments to download.

The first version of the migration transfers the metadata only (decision of 20/11/2026): without --with-files
the version records have no files[].

Run from the repository root:

    python3 -m src.mapeo.geonetwork_mapping [--with-files]
"""
import argparse
from pathlib import Path

from src.config import Config
from src.formato.geonetwork_format import map_geografico_inventory
from src.formato.utilitarios.map_inventory import attach_inventory_data
from src.mapeo.geonetwork import dataverse_check, dataverse_payload, gn_mapping, gn_source
from src.mapeo.reconstruct_mapping import load_dv_schemas
from src.utilitarios.files import BASE_DIR, read_csv, write_csv, write_json
from src.utilitarios.logger import logger

config = Config()

BLOCKS = ["citation", "geospatial", "geographic", "institutional", "externalReferences"]
VERSION = dataverse_payload.VERSION
DATE_SOURCE = "create_time, release_time, dataset_publication_date: createDate; last_update_time: changeDate"


def read_harvest(data_dir):
    """All harvested records as source-side dicts, with the relations between records taken from the XML."""
    variables = gn_source.read_variables(gn_mapping.TABLES_DIR / "gn_variables.csv")
    records = {p.stem: gn_source.read_record(p.stem, data_dir, variables)
               for p in sorted((data_dir / "xml").glob("*.json"))}
    related = gn_mapping.related_from_links(records)  # la cosecha no descarga /related
    for uuid, record in records.items():
        record["related"] = related[uuid]
    return records


def version_dates_row(uuid, gn_info, draft):
    """Row of version_dates.csv (decision of 20/11/2026): dates of the GeoNetwork record (geonet:info).

    The SQL script run after the load does not apply the rows of the drafts (draft = True): their dates are
    left to curation.
    """
    created, changed = gn_info.get("create_date", ""), gn_info.get("change_date", "")
    return {"source_id": uuid, "version": VERSION, "draft": draft,
            "create_time": created, "release_time": created, "last_update_time": changed,
            "dataset_publication_date": created[:10], "date_source": DATE_SOURCE}


def map_records(with_files=False):
    """Writes the version records and the load tables of all migrated GeoNetwork records."""
    data_dir = BASE_DIR / config.gn_data_dir
    missing = [name for name in gn_mapping.TABLES if not (gn_mapping.TABLES_DIR / name).is_file()]
    if missing:  # las tablas no están en el repositorio: se copian a mano (tablas/README.md)
        raise FileNotFoundError(f"Faltan tablas en {gn_mapping.TABLES_DIR}: {', '.join(missing)} "
                                "(ver src/mapeo/geonetwork/tablas/README.md)")
    metadata_dir = Path(config.gn_data_dir) / config.metadata_dir

    records = read_harvest(data_dir)
    excluded = {row["uuid"] for row in read_csv(gn_mapping.TABLES_DIR / "excluded_records.csv")}
    # todos los registros se leen: los servicios hacen falta para las relaciones y los puntos de acceso
    migrated = {u: r for u, r in records.items() if gn_source.migrated(r, excluded)}
    additions = gn_mapping.service_additions([r for u, r in records.items() if u not in migrated], migrated)
    logger.info(f"{len(records)} registros en la cosecha, {len(migrated)} se migran")

    full_index = map_geografico_inventory(config.i2d_inventory)
    gn_info = {row["uuid"]: row for row in read_csv(data_dir / "inventory" / "inventory.csv")}
    tables = gn_mapping.load_tables()
    tsv_schema = load_dv_schemas()

    problems, plan, dates, downloads = {}, [], [], []
    for uuid, record in migrated.items():
        inventory = attach_inventory_data(full_index, uuid, "geografico")["inventory"]
        fields = gn_mapping.dataverse_fields(record, tables, inventory, additions)
        found = dataverse_check.check_fields(fields, tsv_schema, BLOCKS)
        if found:
            problems[uuid] = found
            logger.error(f"Registro {uuid}: {len(found)} problemas frente a las definiciones de los bloques")
            continue  # un registro con problemas no da registro de versión
        options = gn_mapping.load_options(record, inventory)
        version_record = dataverse_payload.version_record(fields, options, tsv_schema, record, inventory, with_files)
        name = dataverse_payload.version_file_name(uuid)
        write_json(version_record, metadata_dir, name)

        row = {"uuid": uuid, "version_file": name, "release": "no" if options["draft"] else "yes",
               "accessType": options["accessType"] or "", "license": options.get("license") or ""}
        if with_files:
            folder = Path(name).stem
            files = version_record["datasetVersion"]["files"]
            row.update(n_files=len(files), restricted_files=sum(f["restricted"] for f in files), files_dir=folder)
            downloads += [{"uuid": uuid, "files_dir": folder, "filename": f["dataFile"]["filename"],
                           "size": f["dataFile"]["filesize"], "url": f["dataFile"]["sourceUrl"]} for f in files]
        plan.append(row)
        dates.append(version_dates_row(uuid, gn_info.get(uuid, {}), options["draft"]))

    write_csv(plan, config.gn_data_dir, "load_plan.csv")
    write_csv(dates, config.gn_data_dir, "version_dates.csv")
    write_json(problems, config.gn_data_dir, "mapping_problems.json")
    if with_files:
        write_csv(downloads, config.gn_data_dir, "files_to_download.csv",
                  fieldnames=["uuid", "files_dir", "filename", "size", "url"])

    files_note = f"{len(downloads)} archivos por descargar" if with_files else "sin archivos (solo metadatos)"
    logger.info(f"{len(plan)} registros de versión en {metadata_dir}, "
                f"{sum(p['release'] == 'no' for p in plan)} borradores, {files_note}, "
                f"{len(problems)} registros con problemas")


def main():
    parser = argparse.ArgumentParser(description="Mapeo de la cosecha de GeoNetwork a registros de versión de Dataverse")
    parser.add_argument("--with-files", action="store_true",
                        help="prepara también los archivos de datos (desactivado en la primera versión de la migración)")
    args = parser.parse_args()
    map_records(with_files=args.with_files)


if __name__ == "__main__":
    main()
