"""Mapping of the Ceiba ingest to Dataverse version records.

Reads the ingest of src/ingest/ceiba_ingest.py (CEIBA_DATA_DIR/METADATA_DIR/<resource>/resource_metadata.json and
CEIBA_DATA_DIR/inventory.csv) and the I2D inventory (INVENTORY_PATH, for the Proyectos Macro rows), applies the
crosswalk with the hand-edited tables of src/mapeo/ceiba/tablas/ (not in the repository: see tablas/README.md),
checks the fields of every record against the block definitions (<block>.tsv in TSV_FILES_PATH, read by
load_dv_schemas()) and writes, in CEIBA_DATA_DIR:

- METADATA_DIR/<resource>-1.0.json: the version record of each migrated resource (only the last published
  version is migrated, as version 1.0, decision of 27/10/2026), {"metadataLanguage", "datasetVersion",
  "inventory_data"}, as for Biocultural and GeoNetwork;
- load_plan.csv: one row per version record: publish after the load or keep as a draft (private IPT resources),
  access type, licence;
- version_dates.csv: the original dates of each version, for the SQL script run after the load;
- curation.csv: the values left out or given a fallback, for the curation phase (one row per case);
- mapping_problems.json: the records whose fields do not pass the checks (they get no version record).

With --with-files, the data files of the DwC-A of each version are also copied, as .tsv/.csv text files, to
CEIBA_DATA_DIR/FILES_DIR/<resource>-1.0/ (the folder src/operaciones/carga/file_upload.py reads) and described in
datasetVersion.files[] (ceiba_files.prepare_files()). Without it the version records have no files[], which
file_upload.py treats as a version without files.

Run from the repository root:

    python3 -m src.mapeo.ceiba_metadata_mapping [--with-files]
"""
import argparse
import re
from pathlib import Path

from src.config import Config
from src.formato.ceiba_format import map_biologico_inventory
from src.ingest.ceiba_ingest import EML_PATTERN
from src.mapeo.ceiba import ceiba_fields, ceiba_files, ceiba_source
from src.mapeo.geonetwork import dataverse_check, dataverse_payload
from src.mapeo.reconstruct_mapping import load_dv_schemas
from src.utilitarios.files import BASE_DIR, read_csv, read_json, write_csv, write_json
from src.utilitarios.logger import logger

config = Config()

VERSION = dataverse_payload.VERSION
DATE_SOURCE = ("create_time: resource.xml created; release_time, dataset_publication_date: first released date of "
               "the versionHistory (first publication in Ceiba); last_update_time: resource.xml modified")
CITATION_YEAR = re.compile(r"\((\d{4})\)|\b((?:19|20)\d{2})\b")


def history_date(value, resource):
    """A date of the versionHistory of resource.xml. XStream writes a date equal to an earlier one as a reference
    (released = {"@reference": "../../../lastPublished"} in 536 entries of the 29/10/2026 copy): resolved to the
    element of the resource it points to."""
    if isinstance(value, dict) and "@reference" in value:
        return ceiba_source.clean(resource.get(value["@reference"].rsplit("/", 1)[-1]))
    return ceiba_source.clean(value)


PUB_DATE = re.compile(r"<pubDate>\s*([^<]*?)\s*</pubDate>")


def first_eml_pubdate(name):
    """(version, pubDate) of the first published EML of the resource (eml-<v>.xml with the lowest version in
    CEIBA_ORIGIN_PATH/<name>/, found with the EML_PATTERN of the ingest), or ("", "") if there is none. Only the
    pubDate is read, with a regular expression, because some archived EML are not valid XML. A curation
    suggestion, not a value of the load (Marius, 25/11/2026)."""
    folder = Path(config.ceiba_origin_path) / name
    versions = []
    for path in folder.glob("eml-*.xml"):
        m = EML_PATTERN.match(path.name)
        if m:
            versions.append(((int(m.group(1)), int(m.group(2) or 0)), path))
    if not versions:
        return "", ""
    (major, minor), path = min(versions)
    found = PUB_DATE.search(path.read_text(encoding="utf-8", errors="replace"))
    return f"{major}.{minor}", ceiba_source.clean(found.group(1)) if found else ""


def version_dates_row(record, draft):
    """Row of version_dates.csv, the dates of version 1.0 of the dataset for the SQL script run after the load
    (destino/fechas_originales.md), on the plan of GeoNetwork (decision of 20/11/2026 there; Marius, 25/11/2026):

    - create_time: creation of the resource in Ceiba (resource.xml created);
    - release_time and dataset_publication_date: first publication of the resource in Ceiba (first released date
      of the versionHistory): version 1.0 is the only version in Dataverse, so its publication is the
      publication of the dataset, as in GeoNetwork (createDate for both);
    - last_update_time: last change of the resource (resource.xml modified), as GeoNetwork's changeDate.

    Informative columns, for comparison: the migrated Ceiba version and its publication date, the EML pubDate and
    the year of Ceiba's citation text (a simple expression: candidates, not a reviewed extraction). The year of
    the citation in Dataverse is the year of dataset_publication_date; when it differs from the citation text,
    the curation phase decides (citation date field, PUT /api/datasets/:persistentId/citationdate).

    The IPT keeps the history of recent versions only: when the first published version is not in the history
    (799 of the 1,091 datasets of the 29/10/2026 copy), the first date of the history is the date of a later
    version. The rule is kept for the SQL script, imperfect, so that the ingest needs no change (Marius,
    25/11/2026): those rows get date_source_status = «historial incompleto», and suggested_publication_date, the
    pubDate of the first EML (first_eml_pubdate()), for the curation phase. The SQL
    script does not apply the rows of the drafts (draft = True): their dates are left to curation. All dates
    of resource.xml are UTC.
    """
    resource = record["resource"]
    history = [h for h in ceiba_source.as_list((resource.get("versionHistory") or {}).get("versionhistory"))
               if isinstance(h, dict)]
    released = {ceiba_source.clean(h.get("version")): history_date(h.get("released"), resource) for h in history}
    migrated = released.get(record["version"]) or ceiba_source.clean(resource.get("lastPublished"))
    first = min((d for d in released.values() if d), default=migrated)
    created = ceiba_source.clean(resource.get("created"))
    modified = ceiba_source.clean(resource.get("modified")) or migrated
    first_version, suggested = first_eml_pubdate(record["name"])
    complete = not first_version or first_version in released or released.get(first_version.removesuffix(".0"))
    citation = ceiba_source.text(record["gbif"].get("citation"))
    year = CITATION_YEAR.search(citation or "")
    return {"source_id": record["name"], "version": VERSION, "draft": draft,
            "create_time": created, "release_time": first, "last_update_time": max(modified, first),
            "dataset_publication_date": first[:10], "date_source": DATE_SOURCE,
            "source_version": record["version"], "source_version_released": migrated,
            "eml_pubdate": ceiba_source.clean(record["dataset"].get("pubDate")),
            "citation_year": (year.group(1) or year.group(2)) if year else "",
            "first_version": first_version, "date_source_status": "completo" if complete else "historial incompleto",
            "suggested_publication_date": "" if complete else suggested}


def map_records(with_files=False):
    # Compared with feature/integracion-ceiba-dataverse-v2 (commit bbdd77d, src/mapeo/validar_integracion_ceiba.py, ejecutar_validacion()):
    # each record is checked against the block definitions (dataverse_check.check_fields(): field names,
    # compound children, repeatability, controlled vocabularies, required fields) rather than by comparing the
    # intermediate dictionary with its reconstruction by unflatten_dataset(), which checks the reconstruction and
    # not the Ceiba rules. It writes the version records and the load tables. Paths come from Config (no relative
    # defaults) and messages go to the project logger.
    """Writes the version records and the load tables of all migrated Ceiba resources (with_files: also the
    data files of the DwC-A)."""
    tables_dir = ceiba_fields.TABLES_DIR
    missing = [name for name in ceiba_fields.TABLES if not (tables_dir / name).is_file()]
    if missing:  # las tablas no están en el repositorio: se copian a mano (tablas/README.md)
        raise FileNotFoundError(f"Faltan tablas en {tables_dir}: {', '.join(missing)} "
                                "(ver src/mapeo/ceiba/tablas/README.md)")
    data_dir = Path(config.ceiba_data_dir)
    raw_dir = BASE_DIR / data_dir / config.metadata_dir
    versions = {r["resource"]: r["latest_version"] for r in read_csv(BASE_DIR / data_dir / "inventory.csv")}
    records = ceiba_source.read_ingest(raw_dir, versions)
    logger.info(f"{len(versions)} recursos en la ingesta, {len(records)} con una versión publicada (se migran)")

    tables = ceiba_fields.load_tables()
    tsv_schema = load_dv_schemas()
    identifiers = ceiba_fields.vocabulary_identifiers(config.tsv_files)
    macro_index = map_biologico_inventory(config.i2d_inventory).get("proyecto_macro", {})

    problems, plan, dates, curation = {}, [], [], []
    for name, record in records.items():
        fields, cases = ceiba_fields.dataverse_fields(record, tables, identifiers, macro_index)
        curation += cases
        found = dataverse_check.check_fields(fields, tsv_schema, ceiba_fields.BLOCKS)
        if found:
            problems[name] = found
            logger.error(f"Recurso {name}: {len(found)} problemas frente a las definiciones de los bloques")
            continue  # un recurso con problemas no da registro de versión
        options = ceiba_fields.load_options(record, fields)
        version_record = dataverse_payload.version_record(fields, options, tsv_schema, record,
                                                          record["inventory"], with_files=False)
        file_name = dataverse_payload.version_file_name(name)
        row_files = {}
        if with_files:
            files_ref = raw_dir / name / "files.json"
            zip_path = read_json(files_ref).get("zip_filepath") if files_ref.is_file() else ""
            entries = []
            if zip_path:
                folder = BASE_DIR / data_dir / config.files_dir / Path(file_name).stem
                entries, file_problems = ceiba_files.prepare_files(
                    zip_path, folder, restricted=options["accessType"] != ceiba_fields.OPEN_ACCESS)
                curation += [{"resource": name, "kind": "data_file", "field": "files", "value": text,
                              "note": "archivo del DwC-A"} for text in file_problems]
            version_record["datasetVersion"]["files"] = entries
            row_files = {"n_files": len(entries), "restricted_files": sum(e["restricted"] for e in entries),
                         "files_dir": Path(file_name).stem if entries else ""}
        write_json(version_record, data_dir / config.metadata_dir, file_name)
        if options["draft"]:
            curation.append({"resource": name, "kind": "private_draft", "field": "", "value": record["ipt_status"],
                             "note": "recurso privado en el IPT: se carga sin publicar"})
        if not options.get("license") and not options.get("termsOfUse"):  # Dataverse no publica sin licencia ni condiciones
            curation.append({"resource": name, "kind": "terms_of_use", "field": "termsOfUse", "value": "",
                             "note": "acceso interno o restringido sin texto de condiciones en el EML: Dataverse no "
                             "lo publica sin licencia ni condiciones de uso; escribirlas antes de publicar"
                             + ("" if options["draft"] else " (¡se publica en la carga!)")})
        plan.append({"resource": name, "source_version": record["version"], "version_file": file_name,
                     "release": "no" if options["draft"] else "yes", "accessType": options["accessType"] or "",
                     "license": options.get("license") or ""} | row_files)
        row_dates = version_dates_row(record, options["draft"])
        dates.append(row_dates)
        if row_dates["date_source_status"] != "completo":
            curation.append({"resource": name, "kind": "publication_date", "field": "dataset_publication_date",
                             "value": row_dates["suggested_publication_date"],
                             "note": f"el historial de resource.xml no tiene la primera versión ({row_dates['first_version']}): "
                                     f"el script SQL usa {row_dates['dataset_publication_date']}; sugerencia: pubDate "
                                     f"de eml-{row_dates['first_version']}.xml"})

    write_csv(plan, data_dir, "load_plan.csv")
    write_csv(dates, data_dir, "version_dates.csv")
    write_csv(curation, data_dir, "curation.csv", fieldnames=["resource", "kind", "field", "value", "note"])
    write_json(problems, data_dir, "mapping_problems.json")
    logger.info(f"{len(plan)} registros de versión en {data_dir / config.metadata_dir}, "
                f"{sum(p['release'] == 'no' for p in plan)} borradores, {len(curation)} casos para la curación, "
                f"{len(problems)} recursos con problemas")


def main():
    parser = argparse.ArgumentParser(description="Mapeo de la ingesta de Ceiba a registros de versión de Dataverse")
    parser.add_argument("--with-files", action="store_true",
                        help="prepara también los archivos de datos de los DwC-A (como .tsv/.csv)")
    args = parser.parse_args()
    map_records(with_files=args.with_files)


if __name__ == "__main__":
    main()
