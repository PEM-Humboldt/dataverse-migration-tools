"""From the Dataverse fields of a GeoNetwork record to the version records and the creation payload.

Follows the structures already used in the repository:

- version record, as format_version_record() of src/formato/biocultural_format.py:
  {"metadataLanguage": "es", "datasetVersion": {...}, "inventory_data": {...}}, saved as
  <identifier>-<version>.json in the metadata folder;
- datasetVersion in the native JSON of Dataverse 6.10: license or custom terms, metadataBlocks with the field
  objects {"typeName", "multiple", "typeClass", "value"} built by unflatten_dataset()
  (src/mapeo/reconstruct_mapping.py) from `tsv_schema` (load_dv_schemas()), and the files in files[].dataFile (filename, filesize,
  contentType, checksum), which src/operaciones/carga/file_upload.py reads to upload them from the folder
  <identifier>-<version>/ of the files directory.

GeoNetwork records have no DOI: each becomes a new dataset (POST /api/dataverses/<collection>/datasets with
{"datasetVersion": ...}), with a single version, here «1.0». The draft flag of load_options() says whether it
is published after the load.

Files (decision of 20/11/2026): the first version of the migration transfers the metadata only, not the data
files. The file functions (dataset_files()) are kept, but they only run with with_files=True; by default the
version records have no files[] key, which file_upload.py treats as a version without files.
"""
import mimetypes
from urllib.parse import unquote

from src.mapeo.reconstruct_mapping import unflatten_dataset

OPEN_ACCESS = "Fully open access (internal/external)"
LICENSE_CC_BY_NC = {"name": "CC BY-NC 4.0", "uri": "https://creativecommons.org/licenses/by-nc/4.0/"}
VERSION = "1.0"


def attachment_name(attachment):
    """File name of a GeoNetwork attachment (the part of its id after /attachments/, URL-decoded)."""
    return unquote(attachment["id"].split("/attachments/", 1)[-1])


def dataset_files(record, restricted):
    """files[] of the version: one entry per attachment of the record, except Windows «Thumbs.db».

    GeoNetwork gives no checksum: dataFile.checksum is filled after the download of the files (MD5 of the
    downloaded file), before file_upload.py. `restricted`: files not downloadable (internal or restricted
    resources, see load_options()).
    """
    files = []
    for attachment in record.get("attachments") or []:
        name = attachment_name(attachment)
        if name.lower() == "thumbs.db":
            continue
        content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        files.append({
            "description": "",
            "categories": [],
            "restricted": restricted,
            "dataFile": {"filename": name, "filesize": int(attachment.get("size") or 0), "contentType": content_type,
                         "checksum": {"type": "MD5", "value": None},
                         "sourceUrl": attachment.get("url")},  # para la descarga; no es un campo de Dataverse
        })
    return files


def dataset_version(fields, options, tsv_schema, record, with_files=False):
    """datasetVersion of the native JSON: license or custom terms, metadata blocks and, with
    with_files=True, the files (first version of the migration: with_files=False, metadata only).

    Licence rule (18/11/2026): open access → CC BY-NC 4.0 (the source's own texts go to an external file,
    options["terms_external_file"]); internal or restricted → no standard licence, the source's texts as
    custom terms (termsOfUse, needs :AllowCustomTermsOfUse = true), and restricted files with file access
    requests enabled (Dataverse requires fileAccessRequest or termsOfAccess for restricted files;
    decision of 20/11/2026: only fileAccessRequest = true, no termsOfAccess nor contactForAccess, which
    are left to curation). Without an access type (record not in the inventory,
    decision of 19/11/2026, or «P»), the files are restricted and the record is a draft (load_options()).
    fileAccessRequest is written even without files: it is a setting of the dataset, ready for the files.
    """
    access = options.get("accessType")
    version = {}
    if access == OPEN_ACCESS:
        version["license"] = dict(LICENSE_CC_BY_NC)
    else:
        if options.get("termsOfUse"):
            version["termsOfUse"] = options["termsOfUse"]
        version["fileAccessRequest"] = True
    version["metadataBlocks"] = unflatten_dataset(fields, tsv_schema)
    if with_files:
        version["files"] = dataset_files(record, restricted=access != OPEN_ACCESS)
    return version


def version_record(fields, options, tsv_schema, record, inventory, with_files=False):
    """Version record of dataverse-migration-tools: {"metadataLanguage", "datasetVersion", "inventory_data"}.
    with_files: include files[] (False in the first version of the migration, metadata only).

    Same record as format_version_record() (src/formato/biocultural_format.py), which writes only to
    BIOCULTURAL_DATA_DIR: the two are to be merged into one function later."""
    return {"metadataLanguage": "es",
            "datasetVersion": dataset_version(fields, options, tsv_schema, record, with_files),
            "inventory_data": inventory}


def version_file_name(uuid, version=VERSION):
    """<identifier>-<version>.json, the name that file_upload.py looks for (identifier = GeoNetwork UUID)."""
    return f"{uuid}-{version}.json"


def create_payload(version_rec):
    """Body of POST /api/dataverses/<collection>/datasets: the datasetVersion without the file entries
    (the files are added afterwards by file_upload.py) and without the helper key sourceUrl."""
    dv = {k: v for k, v in version_rec["datasetVersion"].items() if k != "files"}
    return {"datasetVersion": dv}
