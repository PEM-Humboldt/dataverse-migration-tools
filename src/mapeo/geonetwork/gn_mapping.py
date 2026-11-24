"""Crosswalk GeoNetwork I2D → Dataverse (tablas/crosswalk.csv) as functions.

Input: the record of gn_source.read_record(), the tables of load_tables(), and the I2D inventory data of the
record in the structure of attach_inventory_data() (src/formato/utilitarios/map_inventory.py), with the sheet
`geografico` built by map_geografico_inventory() (src/formato/geonetwork_format.py). Output: Dataverse field values in simple
form (string or list of strings; dict or list of dicts for compounds).
"""
import html
import re
import unicodedata
from pathlib import Path
from urllib.parse import quote

from src.utilitarios.files import read_csv

INSTITUTE = "Instituto de Investigación de Recursos Biológicos Alexander von Humboldt"
INSTITUTE_ROR = "https://ror.org/026dk4f10"
INSTITUTE_ABBREVIATION = "IAvH"
INSTITUTE_URL = "https://www.humboldt.org.co"
INSTITUTE_LOGO = "https://raw.githubusercontent.com/SIB-Colombia/logos/main/socio-SiB-iavh.png"
DEFAULT_CONTACT_EMAIL = "i2d@humboldt.org.co"
# tablas editadas a mano: tienen datos de los registros (nombres, títulos, registros privados), así que no se
# publican en el repositorio (git las ignora por la regla *.csv); se copian a mano, ver tablas/README.md
TABLES_DIR = Path(__file__).resolve().parent / "tablas"
# tablas que lee el código (crosswalk.csv es la referencia de las reglas: no la lee ninguna función)
TABLES = ("gn_variables.csv", "party_roles.csv", "organisations.csv", "people.csv", "citation_mentions.csv",
          "srs_equivalences.csv", "format_equivalences.csv", "excluded_records.csv")
GN_RECORD_URL = "https://geonetwork.humboldt.org.co/geonetwork/srv/spa/catalog.search#/metadata/"
# campos de tipo textbox de los bloques (fieldType en los .tsv), salvo wkt (una geometría): Dataverse 6.10.1 los
# muestra como HTML y no muestra los saltos de línea, así que se escriben en HTML (ver to_html())
TEXTBOX_FIELDS = frozenset({
    "dsDescriptionValue", "publicationCitation", "notesText", "seriesInformation", "relatedMaterial", "relatedDatasets",
    "dataSources", "originOfSources", "characteristicOfSources", "accessToSources", "geographicCoverageDescription",
    "geogPurpose", "attributeDescription", "geographicQualityControl", "lineage", "geographicBiases",
    "projectDescription", "projectDesignDescription", "projectStudyArea", "projectFunding", "acknowledgement",
    "citationText", "externalReferenceNote"})
# campos de tipo url de los bloques (fieldType en los .tsv): Dataverse 6.10.1 no acepta una URL con espacios o
# letras con tilde (p. ej. un adjunto «HOJA METODOLÓGICA.pdf»), así que se codifican con % (ver quote_url())
URL_FIELDS = frozenset({
    "alternativeURL", "keywordTermURI", "keywordVocabularyURI", "topicClassVocabURI", "publicationURL", "producerURL",
    "producerLogoURL", "distributorURL", "distributorLogoURL", "illustrationFile", "externalReferenceURL"})
# caracteres que quote_url() deja como están: los reservados de las URL (RFC 3986) y «%» (lo ya codificado)
URL_SAFE = ":/?#[]@!$&'()*+,;=%~"


def load_tables(mapping_dir=TABLES_DIR, mentions_dir=TABLES_DIR):
    """Tables used by the functions: party roles, people, organisations, equivalences, credit mentions."""
    m, d = Path(mapping_dir), Path(mentions_dir)
    return {
        "party_roles": read_csv(m / "party_roles.csv"),
        "people": read_csv(m / "people.csv"),
        "organisations": read_csv(m / "organisations.csv"),
        "srs": read_csv(m / "srs_equivalences.csv"),
        "formats": read_csv(m / "format_equivalences.csv"),
        "mentions": read_csv(d / "citation_mentions.csv"),
    }


def clean(text):
    """Text with whitespace runs (line breaks included) reduced to one space, stripped."""
    return " ".join(str(text if text is not None else "").split())  # las celdas de Excel pueden no ser texto


def norm_key(text):
    """Comparison key: lower case, without accents or punctuation, single spaces."""
    text = unicodedata.normalize("NFKD", (text or "").lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^\w\s]", " ", text).split())


def unique(items, key=lambda x: x):
    """Items without repetitions (first occurrence kept, order preserved)."""
    seen, out = set(), []
    for item in items:
        k = key(item)
        if k not in seen:
            seen.add(k)
            out.append(item)
    return out


def vals(record, *names):
    """All values of the given variables, in the order of the names."""
    return [v for name in names for v in record["values"].get(name, [])]


def first(record, *names):
    """First value of the first variable that has one, or None."""
    found = vals(record, *names)
    return found[0] if found else None


def path_steps(position):
    """Steps of an indexed path: [(name, index), …] (index 1 when not written)."""
    steps = []
    for step in position.split("/"):
        m = re.fullmatch(r"(.+?)\[(\d+)\]", step)
        steps.append((m.group(1), int(m.group(2))) if m else (step, 1))
    return steps


def groups(record, names, anchor):
    """Values of several variables grouped by the repeated element `anchor` (e.g. 'gmd:descriptiveKeywords').

    Returns a list of {variable: [values]} in document order, one per occurrence of the anchor element;
    values outside any anchor element are ignored.
    """
    found = {}
    for name in names:
        for value, position in zip(record["values"].get(name, []), record["positions"].get(name, [])):
            steps = path_steps(position.split("/@")[0])
            idx = next((i for i, (step, _) in enumerate(steps) if step == anchor), None)
            if idx is None:
                continue
            key = tuple(n for _, n in steps[: idx + 1])
            found.setdefault(key, {}).setdefault(name, []).append(value)
    return [found[k] for k in sorted(found)]


def iso_date(value):
    """Date as YYYY, YYYY-MM or YYYY-MM-DD (the time of a DateTime is dropped); None if not a date."""
    m = re.match(r"\s*(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", value or "")
    if not m:
        return None
    return "-".join(p for p in m.groups() if p)


def institute_names(organisations):
    """Spellings of organisation_name whose canonical_name is the Institute (tablas/organisations.csv)."""
    names = {norm_key(r["organisation_name"]) for r in organisations if r["canonical_name"] == INSTITUTE}
    return names | {norm_key(INSTITUTE)}


def ror_by_name(organisations):
    """{normalised organisation name or canonical name: ROR URL} for the rows with a `ror`."""
    out = {}
    for r in organisations:
        if r["ror"]:
            out[norm_key(r["organisation_name"])] = r["ror"]
            out[norm_key(r["canonical_name"])] = r["ror"]
    out[norm_key(INSTITUTE)] = INSTITUTE_ROR
    return out


def citation_dates(record):
    """{date type: first date} of the resource citation (cit_date / cit_datetime with cit_date_type)."""
    out = {}
    for g in groups(record, ["cit_date", "cit_datetime", "cit_date_type"], "gmd:date"):
        date = iso_date((g.get("cit_date") or g.get("cit_datetime") or [None])[0])
        kind = (g.get("cit_date_type") or [""])[0]
        if date and kind and kind not in out:
            out[kind] = date
    return out


def map_title(record):
    """citation/title: cleaned title (read in SRV/ for the services migrated as datasets)."""
    title = first(record, "cit_title")
    return clean(title) if title else None


def map_alternative_titles(record):
    """citation/alternativeTitle: alternate titles different from the title."""
    title = norm_key(map_title(record))
    return unique([clean(t) for t in vals(record, "cit_alt_title") if norm_key(t) and norm_key(t) != title], norm_key)


def http_urls(texts):
    """Only the texts that are http(s) URLs."""
    return unique([clean(t) for t in texts if re.match(r"https?://", clean(t))])


def map_alternative_urls(record):
    """citation/alternativeURL: the http(s) URLs of md_dataset_uri (template texts are not copied)."""
    return http_urls(vals(record, "md_dataset_uri"))


def map_description(record):
    """citation/dsDescription: Spanish abstract, with the publication date (else revision, else creation)."""
    abstract = first(record, "id_abstract")
    if not abstract:
        return None
    dates = citation_dates(record)
    entry = {"dsDescriptionValue": abstract.strip()}
    date = dates.get("publication") or dates.get("revision") or dates.get("creation")
    if date:
        entry["dsDescriptionDate"] = date
    return [entry]


KEYWORD_TYPES = {"theme": "Tema", "place": "Lugar", "temporal": "Temporal", "discipline": "Disciplina",
                 "stratum": "Estrato", "instrument": "Instrumento", "project": "Proyecto"}
THESAURUS_URIS = {
    "GEMET - Thesaurus de términos ambientales": "https://www.eionet.europa.eu/gemet/",
    "GEMET - INSPIRE themes": "https://www.eionet.europa.eu/gemet/en/inspire-themes/",
    "GCMD - Instruments": "https://gcmd.earthdata.nasa.gov/kms/concepts/concept_scheme/instruments",
    "GeoNames": "https://www.geonames.org/",
}


def map_keywords(record):
    """citation/keyword: one entry per keyword of any type; vocabulary = thesaurus title, else the type in Spanish."""
    entries = []
    names = ["id_keyword", "id_keyword_type", "id_keyword_thesaurus"]
    for g in groups(record, names, "gmd:descriptiveKeywords"):
        thesaurus = clean((g.get("id_keyword_thesaurus") or [""])[0])
        kind = (g.get("id_keyword_type") or [""])[0]
        vocabulary = thesaurus or KEYWORD_TYPES.get(kind, "")
        for word in g.get("id_keyword", []):
            entry = {"keywordValue": clean(word)}
            if vocabulary:
                entry["keywordVocabulary"] = vocabulary
            if thesaurus in THESAURUS_URIS:
                entry["keywordVocabularyURI"] = THESAURUS_URIS[thesaurus]
            if entry["keywordValue"]:
                entries.append(entry)
    return unique(entries, lambda e: (norm_key(e["keywordValue"]), e.get("keywordVocabulary", "")))


def map_notes(record):
    """citation/notesText: one line per filled element, `credit: …`, `otherCitationDetails: …`, `supplementalInformation: …`."""
    lines = []
    for label, name in (("credit", "id_credit"), ("otherCitationDetails", "cit_other_details"),
                        ("supplementalInformation", "id_supplemental_info")):
        lines += [f"{label}: {clean(v)}" for v in vals(record, name) if clean(v)]
    return "\n".join(lines) or None


LANGUAGES = {"spa": "Spanish, Castilian", "spanish": "Spanish, Castilian", "espanol": "Spanish, Castilian",
             "es": "Spanish, Castilian", "eng": "English", "english": "English", "en": "English"}


def map_language(record):
    """citation/language: language of the resource, else of the metadata, as a value of the `language` vocabulary."""
    for value in vals(record, "id_language", "id_language_text", "md_language"):
        found = LANGUAGES.get(norm_key(value))
        if found:
            return [found]
    return None


def map_citation_simple(record):
    """Simple fields of the citation block (without parties, authors and keywords)."""
    dates = citation_dates(record)
    fields = {
        "title": map_title(record),
        "alternativeTitle": map_alternative_titles(record),
        "alternativeURL": (map_alternative_urls(record) or [None])[0],
        "dsDescription": map_description(record),
        "subject": ["Earth and Environmental Sciences"],
        "keyword": map_keywords(record),
        "notesText": map_notes(record),
        "language": map_language(record),
        "productionDate": dates.get("creation"),
        "distributionDate": dates.get("publication"),
    }
    return {k: v for k, v in fields.items() if v}


SECTION_ORDER = ["cited", "point_of_contact", "metadata_contact", "distributor", "other"]
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def valid_email(text):
    """First valid email in the text (lower case), or '' (template texts and «@humboldt.org.co» are not emails)."""
    m = EMAIL.search(text or "")
    return m.group(0).lower() if m else ""


def role_targets(party_roles):
    """{(section, role): [(dataverse field, contributor type)]} from tablas/party_roles.csv."""
    out = {}
    for r in party_roles:
        out.setdefault((r["section"], r["role"]), []).append((r["dv_field"], r["contributor_type"]))
    return out


def not_persons(people):
    """Spellings of individualName marked not_person = TRUE in tablas/people.csv."""
    return {clean(r["individual_name"]) for r in people if r["not_person"].upper() == "TRUE"}


def party_entry(party, no_person):
    """(name, affiliation, email, url) of a party: the person, else (or if not a person) the organisation."""
    person, org = clean(party["individual_name"]), clean(party["organisation_name"])
    if person and person not in no_person:
        return person, org, valid_email(party["email"]), clean(party["url"])
    return org, "", valid_email(party["email"]), clean(party["url"])


def assign_parties(record, tables):
    """{(dataverse field, contributor type): [(name, affiliation, email, url)]}, one entry per name (see the rules above)."""
    targets, no_person = role_targets(tables["party_roles"]), not_persons(tables["people"])
    chosen = {}
    for party in record["parties"]:
        name, affiliation, email, url = party_entry(party, no_person)
        if not name:
            continue
        completeness = sum(bool(x) for x in (affiliation, email, url, clean(party["position_name"])))
        rank = SECTION_ORDER.index(party["section"]) if party["section"] in SECTION_ORDER else len(SECTION_ORDER)
        for target in targets.get((party["section"], party["role"]), []):
            key = (target, name)
            candidate = ((completeness, -rank), (name, affiliation, email, url))
            if key not in chosen or candidate[0] > chosen[key][0]:
                chosen[key] = candidate
    out = {}
    for (target, name), (_, entry) in sorted(chosen.items(), key=lambda kv: list(chosen).index(kv[0])):
        out.setdefault(target, []).append(entry)
    return out


def is_institute(name, institute_spellings):
    """True if the organisation name is a spelling of the Institute (tablas/organisations.csv)."""
    return norm_key(name) in institute_spellings


def map_parties(record, tables):
    """citation/datasetContact, producer, contributor and distributor."""
    assigned = assign_parties(record, tables)
    institute = institute_names(tables["organisations"])
    fields = {}
    contacts = [dict({"datasetContactName": n, "datasetContactEmail": e or DEFAULT_CONTACT_EMAIL},
                     **({"datasetContactAffiliation": a} if a else {}))
                for n, a, e, _ in assigned.get(("datasetContact", ""), [])]
    producers = []
    for n, a, _, _ in assigned.get(("producer", ""), []):
        entry = {"producerName": n}
        if a:
            entry["producerAffiliation"] = a
        if not a and is_institute(n, institute):
            entry.update(producerAbbreviation=INSTITUTE_ABBREVIATION, producerURL=INSTITUTE_URL,
                         producerLogoURL=INSTITUTE_LOGO)
        producers.append(entry)
    contributors = [{"contributorName": n, "contributorType": t}
                    for (f, t), entries in assigned.items() if f == "contributor" for n, _, _, _ in entries]
    distributors = []
    for n, a, _, url in assigned.get(("distributor", ""), []):
        entry = {"distributorName": n}
        if a:
            entry["distributorAffiliation"] = a
        if url:
            entry["distributorURL"] = url
        if not a and is_institute(n, institute):
            entry.update(distributorAbbreviation=INSTITUTE_ABBREVIATION, distributorLogoURL=INSTITUTE_LOGO)
        distributors.append(entry)
    for field, value in (("datasetContact", contacts), ("producer", producers),
                         ("contributor", contributors), ("distributor", distributors)):
        if value:
            fields[field] = value
    return fields


def map_authors(record, tables):
    """citation/author: people and institutions credited at the start of `credit`, else the Institute; ROR when known."""
    rors = ror_by_name(tables["organisations"])
    names = unique([clean(r["author_name"] or r["institution"]) for r in tables["mentions"]
                    if r["uuid"] == record["uuid"] and r["field"] == "credit" and (r["author_name"] or r["institution"])])
    authors = []
    for name in names or [INSTITUTE]:
        entry = {"authorName": name}
        ror = rors.get(norm_key(name))
        if ror:
            entry.update(authorIdentifierScheme="ROR", authorIdentifier=ror)
        authors.append(entry)
    return authors


def map_geospatial(record):
    """geospatial: country (fixed «Colombia»), coverage description and bounding boxes, copied as they are."""
    fields = {"geographicCoverage": [{"country": "Colombia"}]}
    descriptions = [clean(d) for d in vals(record, "id_extent_description") if norm_key(d) not in ("", "ground condition")]
    if descriptions:
        fields["geographicCoverageDescription"] = descriptions[0]
    boxes = []
    for prefix in ("id_bbox_", "srv_bbox_"):
        names = [prefix + s for s in ("west", "east", "north", "south")]
        for g in groups(record, names, "gmd:geographicElement"):
            box = {target: g[prefix + side][0] for side, target in (("west", "westLongitude"), ("east", "eastLongitude"),
                   ("north", "northLatitude"), ("south", "southLatitude")) if g.get(prefix + side)}
            if box:
                boxes.append(box)
    if boxes:
        fields["geographicBoundingBox"] = unique(boxes, lambda b: tuple(sorted(b.items())))
    return fields


TOPOLOGY_ORDER = ["abstract", "geometryOnly", "topology1D", "planarGraph", "fullPlanarGraph", "surfaceGraph",
                  "fullSurfaceGraph", "topology3D", "fullTopology3D"]
UNITS = {"m": "m", "meter": "m", "metre": "m", "metros": "m", "km": "km", "deg": "degree", "degree": "degree",
         "degrees": "degree", "grados": "degree", "arc second": "arc-second", "arcsec": "arc-second"}
IMAGE_FORMATS = {"png": "png", "jpg": "jpeg", "jpeg": "jpeg", "gif": "gif", "tif": "tiff", "tiff": "tiff", "svg": "svg"}
SOFTWARE_VERSION = re.compile(r"\d+(?:\.\d+)+")


def map_software(record):
    """geographic/geogSoftware: one entry per program; texts are split on «;».

    Name: the text before the first version number (d.d…), or the whole text if there is none; version: that
    number. Texts without letters («1.0») are skipped. Template texts are copied as they are (curation).
    """
    entries = []
    for text in vals(record, "dist_format_version", "id_format_version", "id_environment"):
        for part in [clean(p) for p in text.split(";")]:
            if not re.search(r"[A-Za-z]", part):
                continue  # «1.0» y otras versiones sin programa
            version = SOFTWARE_VERSION.search(part)
            name = clean(part[: version.start()] if version else part).strip(" ,-:(")
            if not name:
                continue
            entry = {"geogSoftwareName": name}
            if version:
                entry["geogSoftwareVersion"] = version.group(0)
            entries.append(entry)
    return unique(entries, lambda e: (norm_key(e["geogSoftwareName"]), e.get("geogSoftwareVersion")))


def map_illustrations(record):
    """geographic/illustration: one entry per distinct image; the large version when there are two sizes."""
    entries = []
    for g in groups(record, ["id_overview_file", "id_overview_description", "id_overview_type"], "gmd:graphicOverview"):
        # las URL «https://…:80/…» se corrigen (el puerto 80 no es el de https)
        file = re.sub(r"^(https://[^/:]+):80/", r"\1/", clean((g.get("id_overview_file") or [""])[0]))
        if not file or file.endswith("raster_s.png"):
            continue
        description = clean((g.get("id_overview_description") or [""])[0])
        kind = norm_key((g.get("id_overview_type") or [""])[0]) or file.rsplit(".", 1)[-1].lower()
        entry = {"illustrationFile": file, "illustrationFormat": IMAGE_FORMATS.get(kind, "other"), "_size": description}
        if description and description not in ("large_thumbnail", "thumbnail"):
            entry["illustrationDescription"] = description
        entries.append(entry)
    if any(e["_size"] == "large_thumbnail" for e in entries):
        entries = [e for e in entries if e["_size"] != "thumbnail"]
    return [{k: v for k, v in e.items() if k != "_size"} for e in unique(entries, lambda e: e["illustrationFile"])]


REPORT_KINDS = ("completeness", "topological", "domain", "positional")
REPORT_PARTS = ("measure", "spec_title", "spec_date", "explanation", "pass")


def map_quality_reports(record):
    """Lines of the quality reports (DQ/gmd:report): «<measure> (<specification>, <date>): <explanation> Conforme: sí/no.»"""
    names = [f"dq_report_{k}_{p}" for k in REPORT_KINDS for p in REPORT_PARTS]
    lines = []
    for g in groups(record, names, "gmd:report"):
        part = {p: clean(next((g[f"dq_report_{k}_{p}"][0] for k in REPORT_KINDS if g.get(f"dq_report_{k}_{p}")), ""))
                for p in REPORT_PARTS}
        source = ", ".join(x for x in (part["spec_title"], part["spec_date"]) if x)
        line = part["measure"] or "Informe de calidad"
        line += f" ({source})" if source else ""
        line += f": {part['explanation']}" if part["explanation"] else ""
        if part["pass"]:
            line += " Conforme: " + ("sí." if part["pass"].lower() == "true" else "no.")
        lines.append(line)
    return lines


def map_lineage(record):
    """geographic/lineage: statement, process steps and sources, each part with a title."""
    parts = []
    for title, names in (("Linaje", ["dq_lineage"]), ("Pasos del proceso", ["dq_step_description"]),
                         ("Fuentes", ["dq_source_title", "dq_source_description"])):
        texts = unique([v.strip() for v in vals(record, *names) if v.strip()])
        if texts:
            parts.append(f"{title}:\n" + "\n".join(texts))
    return "\n\n".join(parts) or None


def map_geographic_simple(record):
    """Fields of the geographic block that come straight from the ISO record."""
    fields = {}
    types = unique(["other" if t == "textTable" else t for t in vals(record, "id_spatial_type")])
    if not types:
        types = (["vector"] if vals(record, "vec_topology", "vec_geometry_type") else []) + \
                (["grid"] if vals(record, "grid_dimensions", "georect_dimensions") else [])
    fields["spatialRepresentationType"] = types
    fields["topicCategory"] = unique(vals(record, "id_topic"))
    fields["presentationForm"] = unique(vals(record, "cit_presentation_form"))
    # geogPurpose y geogDatasetStatus no son repetibles: todos los propósitos en un texto, el primer estado
    fields["geogPurpose"] = "\n\n".join(unique([v.strip() for v in vals(record, "id_purpose") if v.strip()])) or None
    fields["geogDatasetStatus"] = first(record, "id_status")
    fields["maintenanceAndUpdateFrequency"] = first(record, "id_maintenance_freq")
    start = iso_date(first(record, "id_time_begin", "id_time_instant"))
    end = iso_date(first(record, "id_time_end", "id_time_instant"))
    if start or end:
        fields["geogDateRange"] = [{k: v for k, v in (("geogStartDate", start), ("geogEndDate", end)) if v}]
    fields["geogSoftware"] = map_software(record)
    fields["equivalentScale"] = unique([re.sub(r"\D", "", v) for v in vals(record, "id_scale_denominator") if re.sub(r"\D", "", v)])
    topologies = [t for t in vals(record, "vec_topology") if t in TOPOLOGY_ORDER]
    fields["topologyLevel"] = max(topologies, key=TOPOLOGY_ORDER.index) if topologies else None
    fields["geometricObjects"] = [
        {k: v for k, v in (("geometricObjectType", (g.get("vec_geometry_type") or [None])[0]),
                           ("geometricObjectCount", (g.get("vec_geometry_count") or [None])[0])) if v}
        for g in groups(record, ["vec_geometry_type", "vec_geometry_count"], "gmd:geometricObjects")]
    distances = []
    for name in ("id_resolution_distance", "grid_resolution", "georect_resolution"):
        for value, unit in zip(record["values"].get(name, []), record.get("units", {}).get(name, [""] * 999)):
            entry = {"resolutionDistanceValue": value}
            if name == "id_resolution_distance" or unit:
                entry["resolutionDistanceUnit"] = UNITS.get(norm_key(unit), "other")
            distances.append(entry)
    fields["resolutionDistance"] = unique(distances, lambda e: tuple(sorted(e.items())))
    coverages = []
    for g in groups(record, ["coverage_content_type", "coverage_attribute", "image_content_type", "image_attribute"],
                    "gmd:contentInfo"):
        entry = {k: v for k, v in (
            ("coverageContentType", (g.get("coverage_content_type") or g.get("image_content_type") or [None])[0]),
            ("attributeDescription", clean((g.get("coverage_attribute") or g.get("image_attribute") or [""])[0])))
            if v}
        if entry:
            coverages.append(entry)
    fields["coverageDescription"] = coverages
    scenes = []
    for title in vals(record, "cit_collective_title"):
        m = re.search(r"Path\s*\d+\s*/\s*Row\s*\d+", title, re.IGNORECASE)
        if m:
            scene = {"pathrow": clean(m.group(0))}
            if any("landsat" in v.lower() for v in vals(record, "image_attribute")):
                scene["pathrowReference"] = "Landsat WRS-2"
            scenes.append(scene)
    fields["satelliteScene"] = scenes
    grids = []
    for prefix in ("grid_", "georect_"):
        for g in groups(record, [prefix + s for s in ("dimensions", "cell_geometry", "transformation_params")],
                        "gmd:spatialRepresentationInfo"):
            entry = {k: v for k, v in (
                ("numberOfDimensions", (g.get(prefix + "dimensions") or [None])[0]),
                ("cellGeometry", (g.get(prefix + "cell_geometry") or [None])[0]),
                ("transformationParameterAvailability",
                 {"true": "TRUE", "false": "FALSE"}.get(((g.get(prefix + "transformation_params") or [""])[0]).lower())))
                if v}
            if entry:
                grids.append(entry)
    # no repetible: la primera descripción de la malla (dos registros tienen dos, 89e8b2dd y e1f04e91)
    fields["gridSpatialRepresentation"] = grids[0] if grids else None
    quality = unique([v.strip() for v in vals(record, "dq_scope_dataset", "dq_scope_other") if v.strip()])
    reports = map_quality_reports(record)
    if reports:
        quality.append("\n".join(reports))  # los informes de calidad, después de la descripción
    fields["geographicQualityControl"] = "\n\n".join(quality) or None
    fields["lineage"] = map_lineage(record)
    fields["illustration"] = map_illustrations(record)
    return {k: v for k, v in fields.items() if v}


def equivalence(table, key, value):
    """{normalised source text: [values]} of an equivalence table; values separated by «;» in the cell."""
    return {clean(r[key]): [clean(v) for v in r[value].split(";") if clean(v)] for r in table}


def map_reference_systems(record, tables):
    """geographic/referenceSystemIdentifier: EPSG integers from tablas/srs_equivalences.csv, without repetitions."""
    table = equivalence(tables["srs"], "code", "epsg")
    return unique([code for text in vals(record, "srs_code", "srs_code_anchor") for code in table.get(clean(text), [])])


def map_formats(record, tables):
    """geographic/distributionFormat: vocabulary values from tablas/format_equivalences.csv, without repetitions."""
    table = equivalence(tables["formats"], "text", "format")
    return unique([f for text in vals(record, "dist_format_name", "id_format_name", "dist_format_spec")
                   for f in table.get(clean(text), [])])


def service_type(text):
    """Web service type of a protocol or format name (OGC:WMS, OGC:WMTS, OGC:WFS, OGC:WCS, other) or None."""
    t = (text or "").upper()
    for kind in ("WMTS", "WMS", "WFS", "WCS"):
        if kind in t:
            return f"OGC:{kind}"
    if t.startswith("OGC:") or "SERVICE" in t:
        return "other"
    return None


def map_online_services(record):
    """geographic/geogOnlineService: service types of the online links and of the WMS/WFS distribution formats."""
    found = [service_type(p) for p in vals(record, "online_protocol")]
    found += [service_type(f) for f in vals(record, "dist_format_name") if norm_key(f) in ("wms", "wfs", "ogc wms", "ogc wfs")]
    return unique([f for f in found if f])


INVALID_URL = re.compile(r"^(undefined|null)$|localhost|ejemplo\.humboldt\.org\.co", re.IGNORECASE)
RECORD_PAGE = re.compile(r"(?:metadata/|uuid=)([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")


OTHER_RECORD_FILE = re.compile(r"/records/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/attachments/")


def reference_type(url, protocol):
    """externalReferenceType of a link.

    PDF or report → This dataset references; GeoNetwork page or data file of another record → Related dataset;
    anything else (OGC services, copies of the data, viewers…) → External Copy of the dataset.
    """
    if url.lower().endswith(".pdf") or "reporte.humboldt.org.co" in url:
        return "This dataset references"
    if RECORD_PAGE.search(url) or OTHER_RECORD_FILE.search(url):
        return "Related dataset"
    return "External Copy of the dataset"


def map_external_references(record):
    """externalReferences/externalReference: the source entry, external links, dataset URIs, related records, citations."""
    uuid = record["uuid"]
    entries = [{"externalReferenceType": "External Copy of the dataset", "externalReferenceURL": GN_RECORD_URL + uuid,
                "citationText": "GeoNetwork I2D", "externalReferenceOtherId": uuid,
                "externalReferenceNote": "Migrado desde GeoNetwork I2D"}]
    for g in groups(record, ["online_url", "online_protocol", "online_name", "online_description"], "gmd:onLine"):
        url = clean((g.get("online_url") or [""])[0])
        if not url or INVALID_URL.search(url) or f"/records/{uuid}/attachments" in url:
            continue
        protocol = clean((g.get("online_protocol") or [""])[0])
        name = clean((g.get("online_name") or [""])[0])
        host = re.sub(r"^https?://([^/]+).*", r"\1", url)
        entry = {"externalReferenceType": reference_type(url, protocol), "externalReferenceURL": url,
                 "citationText": name or clean(f"{protocol if protocol not in ('null', 'undefined') else ''} {host}")}
        m = RECORD_PAGE.search(url) or OTHER_RECORD_FILE.search(url)
        if m:
            entry["externalReferenceOtherId"] = m.group(1)
        description = clean((g.get("online_description") or [""])[0])
        if description:
            entry["externalReferenceNote"] = description
        if protocol and protocol not in ("null", "undefined"):
            entry["externalFileFormat"] = protocol
        entries.append(entry)
    for url in map_alternative_urls(record):
        entries.append({"externalReferenceType": "External Copy of the dataset", "externalReferenceURL": url,
                        "citationText": re.sub(r"^https?://([^/]+).*", r"\1", url)})
    for rel_type, items in (record.get("related") or {}).items():
        if rel_type in ("onlines", "thumbnails") or not items:
            continue
        for item in items if isinstance(items, list) else [items]:
            target = item.get("id", "")
            if not re.fullmatch(r"[0-9a-f-]{36}", target or ""):
                continue
            title = next((t for t in (item.get("title") or {}).values() if t), "")
            entries.append({"externalReferenceType": "Related dataset", "externalReferenceURL": GN_RECORD_URL + target,
                            "citationText": clean(title) or target, "externalReferenceOtherId": target})
    for text in vals(record, "cit_other_details"):
        entries.append({"externalReferenceType": "Citation", "citationText": clean(text)})
    return unique(entries, lambda e: e.get("externalReferenceURL") or e["citationText"])


def related_from_links(records):
    """Relations between records rebuilt from the XML links of all harvested records (services included).

    The harvest of dataverse-migration-tools has no /related. Same shape as GeoNetwork's /related (types services,
    datasets, sources, parent, children, siblings, associated; items {"id": uuid, "title": {"spa": title}}),
    which map_external_references() reads. Only targets that are among `records` are kept. Returns {uuid: related}.
    """
    out = {u: {} for u in records}

    def add(source, kind, target):
        if source in records and target in records and target != source:
            title = (records[target]["values"].get("cit_title") or [""])[0]
            items = out[source].setdefault(kind, [])
            if all(i["id"] != target for i in items):
                items.append({"id": target, "title": {"spa": title}})
    for uuid, record in records.items():
        links = record.get("links", {})
        for target in links.get("operates_on", []):
            add(uuid, "datasets", target)
            add(target, "services", uuid)
        for target in links.get("sources", []):
            add(uuid, "sources", target)
        for target in links.get("parent", []):
            add(uuid, "parent", target)
            add(target, "children", uuid)
        for target in links.get("aggregates", []):
            add(uuid, "siblings", target)
            add(target, "associated", uuid)
    return out


def service_additions(service_records, dataset_records):
    """Access points of the service-level records (md_scope = service) that the datasets they operate on lack.

    Returns {dataset uuid: {"geogOnlineService": [types], "externalReference": [entries]}}: only the missing base
    URLs (without the query) and their service types; the layer (link name) goes to citationText and the
    protocol to externalFileFormat (rule of 12/11/2026, see «Registros de servicios web» in 04_mapping.qmd).
    """
    additions = {}
    for service in service_records:
        if "service" not in service["values"].get("md_scope", []):
            continue
        targets = unique([m.group(0) for href in vals(service, "srv_operates_on")
                          for m in [re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", href)] if m])
        links = groups(service, ["online_url", "online_protocol", "online_name"], "gmd:onLine")
        for target in targets:
            dataset = dataset_records.get(target)
            if dataset is None:
                continue
            have = {clean(u).split("?")[0] for u in vals(dataset, "online_url")}
            for g in links:
                protocol = clean((g.get("online_protocol") or [""])[0])
                kind = service_type(protocol)
                base = clean((g.get("online_url") or [""])[0]).split("?")[0]
                if not kind or not base or base in have:
                    continue
                add = additions.setdefault(target, {"geogOnlineService": [], "externalReference": []})
                add["geogOnlineService"] = unique(add["geogOnlineService"] + [kind])
                add["externalReference"].append({
                    "externalReferenceType": "External Copy of the dataset", "externalReferenceURL": base,
                    "citationText": clean((g.get("online_name") or [""])[0]) or kind, "externalFileFormat": protocol})
                have.add(base)
    return additions


ACCESS_TYPES = {"Libre a nivel interno y externo": "Fully open access (internal/external)",
                "Libre a nivel interno": "Internal open access",
                "Libre a nivel interno con notificación previa": "Internal open access",
                "Restringido temporalmente": "Restricted"}
CONTRACT_PS = re.compile(r"[0-9A-Za-z][0-9A-Za-z/-]*-\d+\s?PS\b")


def map_institutional(inventory):
    """institutional: accessType, project and contractor, from the inventory data of the record.

    `inventory`: the value of «inventory» that attach_inventory_data() adds to the resource:
    {"geografico": {...}, "proyecto_macro_detalle": {...}, "general": {...}}, or {} if the record is not in it.
    """
    geo = inventory.get("geografico") or {}
    if not geo:
        return {}
    fields = {}
    access = ACCESS_TYPES.get(clean(geo.get("tipo_acceso")))
    if access:
        fields["access"] = {"accessType": access}
    macro = inventory.get("proyecto_macro_detalle") or {}
    code = clean(geo.get("proyecto_macro"))
    if code and macro:  # el código es la celda «Proyecto Macro» entera; sin fila en Proyectos Macro: vacío
        fields["project"] = [{k: clean(v) for k, v in (("projectName", macro.get("nombre_diego")),
                                                       ("projectShortName", macro.get("nombre_corto")),
                                                       ("projectID", code), ("projectDescription", macro.get("objeto")))
                              if clean(v)}]
    codes = [re.sub(r"\s", "", c) for c in CONTRACT_PS.findall(clean(geo.get("contrato_convenio")))]
    names = [clean(n) for n in re.split(r"[;\n]|\s+y\s+|,", str(geo.get("contratista") or "")) if clean(n)]
    if codes and len(codes) == len(names):
        fields["contractor"] = [{"contractCode": c, "contractorName": n} for c, n in zip(codes, names)]
    return fields


def load_options(record, inventory):
    """Information for the load, outside the metadata blocks: draft, licence and terms of use.

    draft: inventory «Estado» = «En Proceso», «(TEMPORAL) Metadato finalizado pero privado» = «SI» or
    «Tipo de acceso» = «P», or the record is not in the inventory (19/11/2026). Licence: open → CC BY-NC 4.0 and the source texts to an external file;
    internal or restricted → the source texts (useLimitation, otherConstraints) as custom terms of use.
    """
    geo = inventory.get("geografico") or {}
    texts = unique([v.strip() for v in vals(record, "id_use_limitation", "id_legal_use_limitation", "id_other_constraints")
                    if v.strip()])
    access = ACCESS_TYPES.get(clean(geo.get("tipo_acceso")))
    draft = (not geo or clean(geo.get("estado")) == "En Proceso" or clean(geo.get("tipo_acceso")) == "P"
             or clean(geo.get("metadato_privado")).upper() == "SI")
    options = {"draft": draft, "accessType": access}
    if access == "Fully open access (internal/external)":
        options.update(license="CC BY-NC 4.0", terms_external_file=texts)
    elif access:
        options.update(license=None, termsOfUse="\n\n".join(texts) or None)
    return options


def to_html(text):
    """Plain text as HTML for a textbox field: one <p> per paragraph (blank line), <br> for the other line breaks,
    & < > escaped. Empty lines and spaces around the lines are dropped."""
    paragraphs = [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    return "".join("<p>" + "<br>".join(html.escape(line.strip(), quote=False) for line in p.splitlines() if line.strip())
                   + "</p>" for p in paragraphs)


def textbox_html(value, name=None):
    """The fields of a block (simple form, compounds included) with the values of TEXTBOX_FIELDS in HTML."""
    if isinstance(value, dict):
        return {key: textbox_html(item, key) for key, item in value.items()}
    if isinstance(value, list):
        return [textbox_html(item, name) for item in value]
    if isinstance(value, str) and name in TEXTBOX_FIELDS:
        return to_html(value)
    return value


def quote_url(url):
    """The URL with the characters Dataverse refuses percent-encoded (UTF-8): spaces, letters with accents and the
    other characters outside URL_SAFE. A valid URL, or one already encoded, does not change."""
    return quote(url, safe=URL_SAFE)


def quote_urls(value, name=None):
    """The fields of a block (simple form, compounds included) with the values of URL_FIELDS encoded (quote_url())."""
    if isinstance(value, dict):
        return {key: quote_urls(item, key) for key, item in value.items()}
    if isinstance(value, list):
        return [quote_urls(item, name) for item in value]
    if isinstance(value, str) and name in URL_FIELDS:
        return quote_url(value)
    return value


def dataverse_fields(record, tables, inventory, additions=None):
    """All Dataverse fields of a record: {block: {field: value}}, plus `additions` from service_additions().

    `inventory`: the inventory data of the record (structure of attach_inventory_data(), see map_institutional()).
    The texts of the textbox fields are written in HTML (to_html()) and the URLs are percent-encoded (quote_url()).
    """
    citation = map_citation_simple(record)
    citation["author"] = map_authors(record, tables)
    citation.update(map_parties(record, tables))
    geographic = map_geographic_simple(record)
    for field, value in (("referenceSystemIdentifier", map_reference_systems(record, tables)),
                         ("distributionFormat", map_formats(record, tables)),
                         ("geogOnlineService", map_online_services(record))):
        if value:
            geographic[field] = value
    references = map_external_references(record)
    extra = (additions or {}).get(record["uuid"])
    if extra:
        geographic["geogOnlineService"] = unique(geographic.get("geogOnlineService", []) + extra["geogOnlineService"])
        references = unique(references + extra["externalReference"],
                            lambda e: e.get("externalReferenceURL") or e["citationText"])
    blocks = {"citation": citation, "geospatial": map_geospatial(record), "geographic": geographic,
              "institutional": map_institutional(inventory),
              "externalReferences": {"externalReference": references}}
    return {block: textbox_html(quote_urls(fields)) for block, fields in blocks.items() if fields}
