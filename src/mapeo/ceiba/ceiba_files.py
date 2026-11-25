"""Data files of a Ceiba version: the data files of its Darwin Core Archive, as text files Dataverse ingests.

Rule (crosswalk, «Archivos de datos»; destino/ingesta_tabular.md): the data of the DwC-A of the last version are
loaded as .tsv/.csv text files so that Dataverse 6.10.1 ingests them as tabular files (it ingests text files
only with the .csv or .tsv extension, not .txt nor .zip). Each data file declared in meta.xml (core and
extensions) is copied out of the archive, unchanged, with the extension of its delimiter: tab → .tsv,
comma → .csv. eml.xml and meta.xml are not loaded (the metadata are in the blocks), nor the .zip itself
(LOAD_ZIP = False, Marius, 25/11/2026): Dataverse 6.10.1 unpacks a .zip sent to /add (tested on 24/11/2026 on the
local instance, destino/carga_api_dataverse.md), so the archive would only be kept inside a ZIP_STORED wrapper,
which this code does not create.

The ingest gives the archive path in files.json (zip_filepath, src/ingest/ceiba_ingest.py). The files are written
to FILES_DIR/<resource>-1.0/, the folder src/operaciones/carga/file_upload.py reads, and described in
datasetVersion.files[] with their size and MD5.
"""
import hashlib
import os
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

# El .zip del DwC-A no se carga (Marius, 25/11/2026). Si algún día se pone en True, falta crear el envolvente
# ZIP_STORED: copiado tal cual, Dataverse lo descomprime al subirlo (destino/carga_api_dataverse.md, 24/11/2026)
LOAD_ZIP = False
DELIMITERS = {"\\t": (".tsv", "text/tab-separated-values"), "\t": (".tsv", "text/tab-separated-values"),
              ",": (".csv", "text/csv")}


def archive_files(zip_path):
    """Data files declared in meta.xml of a DwC-A: [{"location", "role" (core / extension), "row_type",
    "delimiter", "encoding", "header_lines"}], in the order of meta.xml."""
    with zipfile.ZipFile(zip_path) as archive:
        root = ET.fromstring(archive.read("meta.xml"))
    found = []
    for element in root:
        role = element.tag.rsplit("}", 1)[-1]
        if role not in ("core", "extension"):
            continue
        location = next((loc.text for files in element if files.tag.endswith("files")
                         for loc in files if loc.tag.endswith("location")), None)
        if location:
            found.append({"location": location.strip(), "role": role, "row_type": element.get("rowType", ""),
                          "delimiter": element.get("fieldsTerminatedBy", "\\t"),
                          "encoding": element.get("encoding", "UTF-8"),
                          "header_lines": element.get("ignoreHeaderLines", "0")})
    return found


def target_name(location, delimiter):
    """File name in Dataverse: the name in the archive with the extension of its delimiter («occurrence.txt» →
    «occurrence.tsv»); unchanged for an unknown delimiter (then Dataverse does not ingest it)."""
    extension = DELIMITERS.get(delimiter, (None, None))[0]
    stem = Path(location).name
    return (Path(stem).stem + extension) if extension else stem


def copy_member(archive, member, path):
    """Copies a member of the archive to `path` (through «<name>.part», renamed at the end); returns (size, MD5)."""
    digest, size = hashlib.md5(), 0
    part = path.with_name(path.name + ".part")
    with archive.open(member) as source, open(part, "wb") as target:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
            size += len(chunk)
            target.write(chunk)
    os.replace(part, path)
    return size, digest.hexdigest()


def prepare_files(zip_path, folder, restricted):
    """Copies the data files of the DwC-A at `zip_path` to `folder` and returns their datasetVersion.files[] entries.

    `restricted`: files not downloadable (access Restricted or Internal open access). Problems (encoding other
    than UTF-8, unknown delimiter) are returned as text in the second element, for the curation list.
    """
    folder.mkdir(parents=True, exist_ok=True)
    entries, problems = [], []
    declared = archive_files(zip_path)
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        for item in declared:
            if item["location"] not in names:
                problems.append(f"{item['location']}: declarado en meta.xml, ausente del archivo")
                continue
            if item["encoding"].upper().replace("-", "") != "UTF8":
                problems.append(f"{item['location']}: codificación {item['encoding']}")
            content_type = DELIMITERS.get(item["delimiter"], (None, "text/plain"))[1]
            if item["delimiter"] not in DELIMITERS:
                problems.append(f"{item['location']}: separador {item['delimiter']!r}, no se ingiere")
            name = target_name(item["location"], item["delimiter"])
            size, md5 = copy_member(archive, item["location"], folder / name)
            entries.append({"description": f"Darwin Core Archive, {item['role']}: {item['row_type']}",
                            "categories": ["Data"], "restricted": restricted,
                            "dataFile": {"filename": name, "filesize": size, "contentType": content_type,
                                         "checksum": {"type": "MD5", "value": md5}}})
    if LOAD_ZIP:
        size = Path(zip_path).stat().st_size
        target = folder / Path(zip_path).name
        digest = hashlib.md5()
        with open(zip_path, "rb") as source, open(target, "wb") as copy:
            while chunk := source.read(1 << 20):
                digest.update(chunk)
                copy.write(chunk)
        entries.append({"description": "Darwin Core Archive original del IPT Ceiba", "categories": ["Data"],
                        "restricted": restricted,
                        "dataFile": {"filename": target.name, "filesize": size, "contentType": "application/zip",
                                     "checksum": {"type": "MD5", "value": digest.hexdigest()}}})
    return entries, problems
