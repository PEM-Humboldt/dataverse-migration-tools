"""Crosswalk IPT Ceiba (EML 2.1.1 / 2.2.0) → Dataverse 6.10.1 blocks, as functions.

The rules are those of the `treatment` column of the validated crosswalk (testCeiba/mapping/crosswalk.csv,
130 rows validated by Marius on 10/11/2026); each function names the rows it applies.

Input: a record of ceiba_source.read_record() (the ingest dictionary of the last published version) and the
tables of load_tables(). Output: {block: {field: value}} in the simple form read by unflatten_dataset()
(src/mapeo/reconstruct_mapping.py): a string or a list of strings; a dict or a list of dicts for compounds.

Principle (Marius, 10/11/2026): the migration is faithful to the source. It applies what the target forces
(vocabularies, formats, single values) and cheap mechanical fixes (split lists, trim); anything that corrects
the source is left to the curation phase, and is written to the curation lists (curation_rows()).
"""
import csv
import re
from pathlib import Path

from src.mapeo.ceiba.ceiba_people import authors_index, eml_contractors, map_authors, map_parties, norm_key
from src.mapeo.ceiba.ceiba_source import as_list, clean, html_paragraphs, paragraphs, text
from src.mapeo.geonetwork.gn_mapping import box_problem, quote_urls
from src.utilitarios.files import read_csv

TABLES_DIR = Path(__file__).resolve().parent / "tablas"
TABLES = ("party_roles.csv", "vocabularies.csv", "restriction_reasons.csv", "citation_authors.csv")
BLOCKS = ["citation", "geospatial", "institutional", "externalReferences", "biologicalMetadata"]

OTHER_ID_AGENCY = "IPT Ceiba (I2D)"
SUBJECT = "Earth and Environmental Sciences"
# Decisión pendiente del equipo (problema de DataCite con el HTML, IQSS/dataverse#12624): False = texto plano con
# los párrafos unidos por un salto de línea (alternativa prevista en la fila dsDescriptionValue)
DESCRIPTION_AS_HTML = True

OPEN_ACCESS = "Fully open access (internal/external)"
INTERNAL_ACCESS = "Internal open access"
RESTRICTED = "Restricted"
FILLERS = {"", "na", "n a", "no aplica", "no", "ninguno", "n7a", "otro"}

DATE = re.compile(r"^\s*(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?(?:[T ].*)?$")


def load_tables(tables_dir=TABLES_DIR):
    """Hand-edited tables read by the functions (tablas/README.md)."""
    d = Path(tables_dir)
    tables = {name.removesuffix(".csv"): read_csv(d / name) for name in TABLES}
    tables["citation_authors_index"] = authors_index(tables["citation_authors"])
    return tables


def vocabulary_identifiers(tsv_dir):
    # Compared with feature/integracion-ceiba-dataverse-v2 (commit bbdd77d, src/mapeo/ceiba_mapping.py, cargar_vocabulario_idiomas()):
    # reads the identifiers of all the controlled vocabularies from the final block definitions in
    # TSV_FILES_PATH (the same folder load_dv_schemas() reads), instead of a copy of citation.tsv in the
    # repository; the language equivalence (spa → «Spanish, Castilian») is the same.
    """{(field, identifier lower-cased): value} of the controlled vocabularies of the block definitions
    (#controlledVocabulary rows of the <block>.tsv files). load_dv_schemas() keeps only the values; the language
    codes (ISO 639-2 «spa») are identifiers."""
    found = {}
    for path in sorted(Path(tsv_dir).glob("*.tsv")):
        with open(path, encoding="utf-8-sig", newline="") as f:
            reading, headers = False, []
            for row in csv.reader(f, delimiter="\t"):
                if not row:
                    continue
                if row[0].strip().startswith("#"):
                    reading = row[0].strip() == "#controlledVocabulary"
                    headers = [h.strip() for h in row]
                    continue
                if reading:
                    r = dict(zip(headers, row))
                    if r.get("identifier"):
                        found[(r["DatasetField"].strip(), r["identifier"].strip().lower())] = r["Value"].strip()
    return found


def iso_date(value):
    # Compared with feature/integracion-ceiba-dataverse-v2 (commit bbdd77d, src/mapeo/ceiba_mapping.py, mapear_fecha_publicacion()):
    # also accepts YYYY and YYYY-MM, which Dataverse 6.10 accepts in a date field (Admin Guide, Metadata
    # Customization, fieldType date); keeping only YYYY-MM-DD leaves out the year-only pubDate.
    """Date as YYYY, YYYY-MM or YYYY-MM-DD (the three forms Dataverse 6.10 accepts for a date field; the time of
    a date-time is dropped), or None when it is not a date (it is then left out and listed for curation)."""
    m = DATE.match(value or "")
    if not m:
        return None
    return "-".join(p for p in m.groups() if p)


def textbox(paras):
    """Paragraphs of a text element as the HTML of a textbox field (crosswalk: «Texto en HTML»)."""
    return html_paragraphs(paras)


# ---------------------------------------------------------------------------------------------------------------
# citation
# ---------------------------------------------------------------------------------------------------------------

GBIF_TYPE_VALUES = {"occurrence", "checklist", "metadata", "samplingevent", "other",
                    "registro biologico", "lista de chequeo", "metadatos", "evento de muestreo", "otro"}
GBIF_SUBTYPE_VALUES = {"specimen", "observation", "inventoryregional", "inventorythematic",
                       "derivedfromoccurrence", "taxonomicauthority", "nomenclatorauthority", "generalinventory",
                       "citation", "other", "especimen", "observacion", "inventario regional",
                       "inventario tematico", "derivado de registros biologicos"}
GBIF_VOCABULARIES = {"gbif_type": ("GBIF Dataset Type Vocabulary", GBIF_TYPE_VALUES),
                     "gbif_subtype": ("GBIF Dataset Subtype Vocabulary", GBIF_SUBTYPE_VALUES)}
URL = re.compile(r"https?://\S+")


def thesaurus_class(thesaurus):
    # Compared with feature/integracion-ceiba-dataverse-v2 (commit bbdd77d, src/mapeo/ceiba_mapping.py, separar_tesauro_uri()):
    # crosswalk row keywordVocabulary. Besides N/A, NA and NO APLICA, the fillers «Otro», «'n/a'»… and the free
    # texts written in the thesaurus box (for example «Registro biológico») are not thesauri: their keywords get
    # no vocabulary. Treating any other text as a vocabulary would give those keywords a vocabulary name.
    """Class of a keywordThesaurus text, as in the keywords profile of testCeiba (02_profile.qmd,
    keywords-profile): gbif_type, gbif_subtype, «sin tesauro» (fillers: N/A, n/a, NA, Otro…), tesauro, otro texto."""
    lower = thesaurus.lower()
    if "dataset subtype vocabulary" in lower:
        return "gbif_subtype"
    if "dataset type vocabulary" in lower:
        return "gbif_type"
    if norm_key(thesaurus) in FILLERS:
        return "sin tesauro"
    if re.search(r"thesaurus|tesauro|vocabular|diccionario|https?://", thesaurus, re.IGNORECASE):
        return "tesauro"
    return "otro texto"


def map_keywords(dataset):
    # Compared with feature/integracion-ceiba-dataverse-v2 (commit bbdd77d, src/mapeo/ceiba_mapping.py, mapear_palabras_clave() and
    # es_palabra_clave_gbif()): same rules for splitting on «;» and «,», for the vocabulary name without its URL
    # and for keeping the occurrence that has a vocabulary. Differences: the duplicate key is the word alone, so
    # a word written in two thesauri appears once (the key word + vocabulary keeps it twice); the GBIF values are
    # also recognised in their Spanish labels («Registro biológico», «Especimen»…, IPT in Spanish); the classes
    # of the thesaurus texts come from thesaurus_class().
    """citation/keyword (rows keywordValue, keywordVocabulary, keywordVocabularyURI).

    All keywords, GBIF type and subtype values included, as written, split on «;» and «,»; repetitions within the
    dataset removed (comparison without accents nor case), keeping the occurrence that has a vocabulary, else the
    first spelling, at the place of the first occurrence (Marius, 25/11/2026). Vocabulary: the
    thesaurus name for a real thesaurus; «GBIF Dataset (Sub)type Vocabulary» for the GBIF values; empty for the
    fillers and for the free words written in the GBIF sets. Vocabulary URI: the URL of the thesaurus text, with
    the same rule.
    """
    entries, seen = [], {}  # seen: norm_key(value) → index in entries
    for keyword_set in as_list(dataset.get("keywordSet")):
        if not isinstance(keyword_set, dict):
            continue
        thesaurus = text(keyword_set.get("keywordThesaurus"))
        cls = thesaurus_class(thesaurus)
        url = URL.search(thesaurus)
        for raw in as_list(keyword_set.get("keyword")):
            for value in (clean(v) for v in re.split(r"[;,]", text(raw))):
                if not value:
                    continue
                entry = {"keywordValue": value}
                if cls in GBIF_VOCABULARIES and norm_key(value) in GBIF_VOCABULARIES[cls][1]:
                    entry["keywordVocabulary"] = GBIF_VOCABULARIES[cls][0]
                    if url:
                        entry["keywordVocabularyURI"] = url.group(0)
                elif cls == "tesauro":
                    name = clean(URL.sub("", thesaurus)).strip(" :-–")
                    if name:
                        entry["keywordVocabulary"] = name
                    if url:
                        entry["keywordVocabularyURI"] = url.group(0)
                key = norm_key(value)
                if key not in seen:
                    seen[key] = len(entries)
                    entries.append(entry)
                elif "keywordVocabulary" in entry and "keywordVocabulary" not in entries[seen[key]]:
                    entries[seen[key]] = entry  # la repetición con vocabulario reemplaza a la palabra libre
    return entries


def map_description(dataset):
    # Compared with feature/integracion-ceiba-dataverse-v2 (commit bbdd77d, src/mapeo/ceiba_mapping.py, mapear_descripcion()):
    # crosswalk rows dsDescriptionValue and dsDescriptionDate. The value is HTML, one <p> per paragraph (textbox
    # rule, destino/textos_html_textbox.md), with the switch DESCRIPTION_AS_HTML for plain text with paragraphs
    # joined by one line break (alternative of the crosswalk while IQSS/dataverse#12624 is open); joining with
    # a blank line matches neither form. dsDescriptionDate is filled with dataset/pubDate.
    """citation/dsDescription (rows dsDescriptionValue, dsDescriptionDate): the abstract, in HTML (or plain text
    with the paragraphs joined by one line break, DESCRIPTION_AS_HTML = False), with the pubDate of the version."""
    paras = paragraphs(dataset.get("abstract"))
    if not paras:
        return []
    entry = {"dsDescriptionValue": textbox(paras) if DESCRIPTION_AS_HTML else "\n".join(paras)}
    date = iso_date(text(dataset.get("pubDate")))
    if date:
        entry["dsDescriptionDate"] = date
    return [entry]


def map_language(dataset, identifiers):
    """citation/language: ISO 639-2 code («spa») → value of the vocabulary by its identifier («Spanish,
    Castilian»). An unknown code is left out."""
    values = []
    for code in as_list(dataset.get("language")):
        value = identifiers.get(("language", text(code).lower()))
        if value and value not in values:
            values.append(value)
    return values


def map_citation(record, tables, identifiers):
    # Compared with feature/integracion-ceiba-dataverse-v2 (commit bbdd77d, src/mapeo/ceiba_mapping.py, construir_citation_intermedio()):
    # the functions return the values of the intermediate format directly ({block: {field: value}}), so
    # typeName, typeClass and multiple come only from the block definitions through unflatten_dataset(); there is
    # no step building complete Dataverse fields and reducing them again (convertir_compuesto()). notesText is
    # a textbox field, so it is written in HTML like the description. title, alternativeTitle, otherId (agency
    # «IPT Ceiba (I2D)», value = @packageId), subject and language follow the same crosswalk rules in both.
    """The citation block of a record, except the people (map_parties()) and the authors (map_authors())."""
    dataset = record["dataset"]
    fields = {"title": text(dataset.get("title"))}
    short_names = [text(v) for v in as_list(dataset.get("shortName")) if text(v)]  # solo EML 2.2.0
    if short_names:
        fields["alternativeTitle"] = short_names
    if record["package_id"]:
        fields["otherId"] = [{"otherIdAgency": OTHER_ID_AGENCY, "otherIdValue": record["package_id"]}]
    fields["dsDescription"] = map_description(dataset)
    fields["subject"] = [SUBJECT]
    fields["keyword"] = map_keywords(dataset)
    notes = paragraphs(dataset.get("additionalInfo"))
    if notes:
        fields["notesText"] = textbox(notes)
    fields["language"] = map_language(dataset, identifiers)
    date = iso_date(text(dataset.get("pubDate")))
    if date:
        fields["distributionDate"] = date
    return fields


# ---------------------------------------------------------------------------------------------------------------
# geospatial
# ---------------------------------------------------------------------------------------------------------------

BOX_SOURCE = {"westLongitude": "westBoundingCoordinate", "eastLongitude": "eastBoundingCoordinate",
              "northLatitude": "northBoundingCoordinate", "southLatitude": "southBoundingCoordinate"}


def map_geospatial(record, curation):
    """geospatial: geographicCoverageDescription and geographicBoundingBox (assigned by field name).

    A box that Dataverse 6.10.1 refuses (West ≥ East, South ≥ North, a side missing or out of range: it rejects
    the whole dataset) is left out and listed for curation; valid boxes are copied as they are, even with a
    positive longitude or swapped coordinates (curation).
    """
    coverage = record["dataset"].get("coverage") if isinstance(record["dataset"].get("coverage"), dict) else {}
    fields, descriptions, boxes = {}, [], []
    for geo in as_list(coverage.get("geographicCoverage")):
        if not isinstance(geo, dict):
            continue
        description = text(geo.get("geographicDescription"))
        if description:
            descriptions.append(description)
        coords = geo.get("boundingCoordinates") if isinstance(geo.get("boundingCoordinates"), dict) else {}
        box = {field: text(coords.get(source)) for field, source in BOX_SOURCE.items() if text(coords.get(source))}
        if not box:
            continue
        problem = box_problem(box)
        if problem:
            curation.append({"resource": record["name"], "kind": "bounding_box", "field": "geographicBoundingBox",
                             "value": " ".join(f"{k}={v}" for k, v in box.items()), "note": problem})
        else:
            boxes.append(box)
    if descriptions:  # campo de un solo valor: las descripciones de varias coberturas se unen en párrafos
        fields["geographicCoverageDescription"] = textbox(descriptions)
    if boxes:
        fields["geographicBoundingBox"] = boxes
    return fields


# ---------------------------------------------------------------------------------------------------------------
# biologicalMetadata
# ---------------------------------------------------------------------------------------------------------------

def vocabulary(tables, field, source):
    """{source value lower-cased: Dataverse value} of tablas/vocabularies.csv for a field and a source."""
    return {r["source_value"].strip().lower(): r["dataverse_value"] for r in tables["vocabularies"]
            if r["field"] == field and r["source"] == source and r["dataverse_value"]}


def map_temporal(record, curation):
    """biologicalMetadata/temporalCoverage: Date (singleDateTime), Date Range (rangeOfDates), Formation period
    (gbif/formationPeriod). A date that is not YYYY, YYYY-MM or YYYY-MM-DD is left out and listed for curation."""
    dataset = record["dataset"]
    coverage = dataset.get("coverage") if isinstance(dataset.get("coverage"), dict) else {}
    entries = []

    def date_of(node, field):
        raw = text((node or {}).get("calendarDate")) if isinstance(node, dict) else ""
        value = iso_date(raw)
        if raw and not value:
            curation.append({"resource": record["name"], "kind": "date", "field": field, "value": raw,
                             "note": "no es una fecha AAAA, AAAA-MM ni AAAA-MM-DD"})
        return value

    for temporal in as_list(coverage.get("temporalCoverage")):
        if not isinstance(temporal, dict):
            continue
        for single in as_list(temporal.get("singleDateTime")):
            value = date_of(single, "simpleCalendarDate")
            if value:
                entries.append({"temporalCoverageType": "Date", "simpleCalendarDate": value})
        for dates in as_list(temporal.get("rangeOfDates")):
            if not isinstance(dates, dict):
                continue
            entry = {"temporalCoverageType": "Date Range"}
            begin, end = date_of(dates.get("beginDate"), "initialCalendarDate"), date_of(dates.get("endDate"),
                                                                                         "finalCalendarDate")
            if begin:
                entry["initialCalendarDate"] = begin
            if end:
                entry["finalCalendarDate"] = end
            if len(entry) > 1:
                entries.append(entry)
    period = text(record["gbif"].get("formationPeriod"))
    if period:
        entries.append({"temporalCoverageType": "Formation period", "formationPeriod": textbox([period])})
    return entries


def map_taxonomic(record, tables, curation):
    """taxonomicCoverageDescription (repeatable: one per taxonomicCoverage) and taxonomicClassification
    (rank translated with tablas/vocabularies.csv, scientific name, common name). A rank missing from the table
    is left out of its entry and listed for curation."""
    coverage = record["dataset"].get("coverage") if isinstance(record["dataset"].get("coverage"), dict) else {}
    ranks = vocabulary(tables, "taxonRankName", "eml")
    descriptions, taxa = [], []
    for taxonomic in as_list(coverage.get("taxonomicCoverage")):
        if not isinstance(taxonomic, dict):
            continue
        general = text(taxonomic.get("generalTaxonomicCoverage"))
        if general:
            descriptions.append(textbox([general]))
        for taxon in as_list(taxonomic.get("taxonomicClassification")):
            if not isinstance(taxon, dict):
                continue
            entry = {"taxonRankValue": text(taxon.get("taxonRankValue")), "commonName": text(taxon.get("commonName"))}
            rank = text(taxon.get("taxonRankName"))
            if rank:
                if rank.lower() in ranks:
                    entry["taxonRankName"] = ranks[rank.lower()]
                else:
                    curation.append({"resource": record["name"], "kind": "vocabulary", "field": "taxonRankName",
                                     "value": rank, "note": "rango sin equivalencia en tablas/vocabularies.csv"})
            entry = {k: v for k, v in entry.items() if v}
            if entry:
                taxa.append(entry)
    fields = {}
    if descriptions:
        fields["taxonomicCoverageDescription"] = descriptions
    if taxa:
        fields["taxonomicClassification"] = taxa
    return fields


def map_methods(dataset):
    """emlMethod (study extent, sampling, quality control: one entry) and emlMethodStep (one per step, numbered)."""
    methods = dataset.get("methods") if isinstance(dataset.get("methods"), dict) else {}
    sampling = methods.get("sampling") if isinstance(methods.get("sampling"), dict) else {}
    extent = sampling.get("studyExtent") if isinstance(sampling.get("studyExtent"), dict) else {}
    quality = methods.get("qualityControl") if isinstance(methods.get("qualityControl"), dict) else {}
    method = {"emlMethodStudyArea": textbox(paragraphs(extent.get("description"))),
              "emlMethodSampling": textbox(paragraphs(sampling.get("samplingDescription"))),
              "emlMethodQualityControl": textbox(paragraphs(quality.get("description")))}
    method = {k: v for k, v in method.items() if v}
    steps = []
    for step in as_list(methods.get("methodStep")):
        description = textbox(paragraphs(step.get("description"))) if isinstance(step, dict) else ""
        if description:
            steps.append({"emlMethodStepNumber": str(len(steps) + 1), "emlMethodStepDescription": description})
    fields = {}
    if method:
        fields["emlMethod"] = [method]
    if steps:
        fields["emlMethodStep"] = steps
    return fields


URI = re.compile(r"^(https?://|urn:lsid:)", re.IGNORECASE)
RNC = re.compile(r"\b(RNC|RCN)\b|registro nacional de colecciones|\bregistro\s+\d+", re.IGNORECASE)  # «RCN: 3», «Registro 3 de 1996»


def map_collections(record, curation):
    """biologicalMetadata/collectionData, one entry per collection of the EML.

    collectionName and parentCollectionIdentifier as written, parent empty for the fillers (official names and
    normalised parents are left to the curation phase, without a collections table: Marius, 25/11/2026);
    collectionIdentifier when it is a URI or a text of the Registro Nacional de Colecciones (copied as is);
    collectionCode for a code, and for another text, copied as is and listed for curation (Marius, 25/11/2026);
    a list of codes («FMB, DUGAND», also separated by «|») becomes several entries, the name and the parent
    only in the first one, and the list goes to curation (which code each written name belongs to).
    """
    entries = []
    for collection in as_list(record["gbif"].get("collection")):
        if not isinstance(collection, dict):
            continue
        name = text(collection.get("collectionName"))
        parent = text(collection.get("parentCollectionIdentifier"))
        parent = "" if norm_key(parent) in FILLERS else parent
        identifier = text(collection.get("collectionIdentifier"))
        base = {"collectionName": name, "parentCollectionIdentifier": parent}
        if not identifier or norm_key(identifier) in FILLERS:
            entries.append(base)
        elif URI.match(identifier) or RNC.search(identifier):
            entries.append(base | {"collectionIdentifier": [identifier]})
        elif re.search(r"[,;|]", identifier):
            codes = [clean(c) for c in re.split(r"[,;|]", identifier) if clean(c)]
            entries.append(base | {"collectionCode": codes[0]})
            entries += [{"collectionCode": c} for c in codes[1:]]
            if len(codes) > 1:
                curation.append({"resource": record["name"], "kind": "collection_codes", "field": "collectionName",
                                 "value": identifier, "note": "lista de códigos separada en entradas: nombre y "
                                 "colección madre solo en la primera; asignar a cada código su nombre"})
        elif " " in identifier:  # otro texto con espacios (ni URI ni RNC): como código, tal como está, y a la curación
            entries.append(base | {"collectionCode": identifier})
            curation.append({"resource": record["name"], "kind": "collection_identifier", "field": "collectionCode",
                             "value": identifier, "note": "identificador de colección que no es un código, un URI "
                             "ni un texto del RNC: copiado como código; revisar qué es"})
        else:
            entries.append(base | {"collectionCode": identifier})
    return [{k: v for k, v in e.items() if v} for e in entries if any(e.values())]


def map_biological(record, tables, curation):
    """The biologicalMetadata block of a record."""
    dataset, resource = record["dataset"], record["resource"]
    fields = {"emlShortName": record["name"]}
    for field in ("coreType", "subtype"):  # solo de resource.xml, sin respaldo en las palabras clave
        raw = clean(resource.get(field))
        value = vocabulary(tables, field, "resource.xml").get(raw.lower()) if raw else None
        if value:
            fields[field] = value
        elif raw:
            curation.append({"resource": record["name"], "kind": "vocabulary", "field": field, "value": raw,
                             "note": "valor sin equivalencia en tablas/vocabularies.csv"})
    for field in ("purpose", "introduction", "gettingStarted"):
        value = textbox(paragraphs(dataset.get(field)))
        if value:
            fields[field] = value
    fields.update(map_taxonomic(record, tables, curation))
    temporal = map_temporal(record, curation)
    if temporal:
        fields["temporalCoverage"] = temporal
    fields.update(map_methods(dataset))
    collections = map_collections(record, curation)
    if collections:
        fields["collectionData"] = collections
    methods = vocabulary(tables, "specimenPreservationMethod", "eml")
    preservation = []
    for raw in (text(v) for v in as_list(record["gbif"].get("specimenPreservationMethod"))):
        value = methods.get(raw.lower())
        if value and value not in preservation:
            preservation.append(value)
        elif raw and not value:
            curation.append({"resource": record["name"], "kind": "vocabulary", "field": "specimenPreservationMethod",
                             "value": raw, "note": "valor sin equivalencia en tablas/vocabularies.csv"})
    if preservation:
        fields["specimenPreservationMethod"] = preservation
    return fields


# ---------------------------------------------------------------------------------------------------------------
# externalReferences
# ---------------------------------------------------------------------------------------------------------------

DOI = re.compile(r"(10\.\d{4,9}/\S+)")
DOI_PREFIX = re.compile(r"^(?:(?:https?://)?(?:dx\.)?doi\.org/|doi\s*:?\s*)", re.IGNORECASE)  # also «DOI : 10.…», «doi.org/10.…»
OTHER_ID = re.compile(r"\b(ISBN|ISSN)\b", re.IGNORECASE)


def doi_of(value):
    """DOI without its prefix (http(s)://doi.org/, doi:), or None when the value is not a DOI."""
    value = clean(value)
    m = DOI.search(DOI_PREFIX.sub("", value))
    return m.group(1).rstrip(".") if m and (DOI_PREFIX.match(value) or value.startswith("10.")) else None


# Página del recurso en Ceiba: la entrada del registro de origen de externalReferences (como GeoNetwork)
CEIBA_RESOURCE_URL = "https://i2d.humboldt.org.co/ceiba/resource?r={name}&v={version}"
SOURCE_NAME = OTHER_ID_AGENCY


def source_reference(record):
    """The source entry of externalReferences, one per dataset, as for GeoNetwork (Marius, 25/11/2026): «External
    Copy of the dataset», the page of the resource in Ceiba, citationText «IPT Ceiba (I2D)», the short name of the
    resource as externalReferenceOtherId (the key of the migration) and the note «Migrado desde IPT Ceiba (I2D)».

    The URL is built from the short name and the migrated version (CEIBA_RESOURCE_URL: the address form of the
    current IPT, https and without «.do», with &v= so that it shows the version held in Dataverse even if the
    resource is republished in Ceiba; Marius, 25/11/2026), and not copied from the EML
    (dataset/distribution/online/url), because the EML address is not reliable: in the copy of 24/11/2026, 152
    last versions have none, and some point to another page or another resource (r=plantilla, an empty r=, the
    SiB Colombia IPT, the management pages of Ceiba), in the old (http, resource.do) or the new form. The link
    stops working when Ceiba is shut down: the curation phase replaces or removes it (curacion.qmd).
    """
    return {"externalReferenceType": "External Copy of the dataset",
            "externalReferenceURL": CEIBA_RESOURCE_URL.format(name=record["name"], version=record["version"]), "citationText": SOURCE_NAME,
            "externalReferenceOtherId": record["name"], "externalReferenceNote": f"Migrado desde {SOURCE_NAME}"}


def map_external_references(record, curation):
    """externalReferences/externalReference: the source entry (source_reference()), «This dataset references» per
    citation of the EML bibliography
    (text; DOI or URL of its identifier) and «External Copy of the dataset» with the SiB Colombia / GBIF DOI of
    the inventory. ISBN and ISSN identifiers go to externalReferenceOtherId as written; a URL written without its
    scheme («www.…») gets https:// and is listed for curation, a malformed one is only listed (Marius,
    25/11/2026); other identifiers (short labels such as «Vallejo et al. 2005», fillers) are not migrated, the
    citation text has the reference."""
    entries = [source_reference(record)]
    bibliography = record["gbif"].get("bibliography") if isinstance(record["gbif"].get("bibliography"), dict) else {}
    for citation in as_list(bibliography.get("citation")):
        citation_value = text(citation)
        if not citation_value:
            continue
        entry = {"externalReferenceType": "This dataset references", "citationText": textbox([citation_value])}
        identifier = clean(citation.get("@identifier")) if isinstance(citation, dict) else ""
        doi = doi_of(identifier)
        if doi:
            entry["externalReferenceDOI"] = doi
        elif re.match(r"^https?://\S+$", identifier):
            entry["externalReferenceURL"] = identifier
        elif re.match(r"^www\.\S+$", identifier, re.IGNORECASE):
            entry["externalReferenceURL"] = "https://" + identifier
            curation.append({"resource": record["name"], "kind": "reference_url", "field": "externalReferenceURL",
                             "value": identifier, "note": "URL escrita sin https://: añadido en la migración; "
                             "comprobar que el enlace funciona"})
        elif re.match(r"^www\.", identifier, re.IGNORECASE):
            curation.append({"resource": record["name"], "kind": "reference_url", "field": "externalReferenceURL",
                             "value": identifier, "note": "URL mal escrita: no migrada"})
        elif OTHER_ID.search(identifier):
            entry["externalReferenceOtherId"] = identifier
        entries.append(entry)
    biologico = (record["inventory"] or {}).get("biologico") or {}
    copy_doi = doi_of(str(biologico.get("doi") or ""))
    if copy_doi:
        entries.append({"externalReferenceType": "External Copy of the dataset", "externalReferenceDOI": copy_doi})
    return entries


# ---------------------------------------------------------------------------------------------------------------
# institutional
# ---------------------------------------------------------------------------------------------------------------

ACCESS_PATTERNS = ((re.compile(r"libre a nivel (?:interno y externo|externo e interno)"), OPEN_ACCESS),
                   (re.compile(r"libre (?:a|en) nivel interno"), INTERNAL_ACCESS),
                   (re.compile(r"restringido temporalmente"), RESTRICTED))
# códigos de contratos de prestación de servicios: terminados en PS (23-22-444-279PS, 24-24-111-182 PS,
# 22-22/444-22/444-279PS…) o con cuatro grupos de cifras sin sufijo (14-13-014-040); los demás (CE, FN, AA-NNN,
# FP44842-109-2016…) son convenios u otros acuerdos
OTHER_CONTRACT = re.compile(r"\d\s?(FN|OS)$", re.I)  # contratos que no son de prestación de servicios
PS_CODE = re.compile(r"\b[0-9A-Za-z][0-9A-Za-z/-]*-\d+\s?PS\b|\b\d{2}-\d{2}-\d{3,4}-\d{3,4}\b(?![\s-]?[A-Za-z])")


def rights_text(dataset):
    """Text of intellectualRights (its paragraphs, links written as «title (url)»)."""
    return " ".join(paragraphs(dataset.get("intellectualRights")))


def access_type(dataset):
    """institutional/access/accessType from the intellectualRights text of the last version (decision of
    06/11/2026): open, internal (with or without prior notification), temporarily restricted; a text without a
    recognisable category, or no text → Restricted."""
    key = " ".join(clean(rights_text(dataset)).lower().split())
    for pattern, value in ACCESS_PATTERNS:
        if pattern.search(key):
            return value
    return RESTRICTED


def split_cell(value):
    """Values of an inventory cell separated by «|» or «;», without fillers (NA, P…)."""
    return [clean(v) for v in re.split(r"[|;]", str(value or "")) if clean(v) and norm_key(v) not in FILLERS | {"p"}]


def map_projects(record, macro_index, curation):
    """institutional/project: two separate entries, never merged (Marius, 10/11/2026).

    (1) The scientific project of the EML: title (left out if it repeats the dataset title), @id, abstract,
        design description, study area, funding text (with the EML 2.2.0 awards appended, one per award).
    (2) The institutional project of the inventory, one entry per «Proyecto Macro» code: projectShortName =
        Proyecto, projectID = the code, projectName = NOMBRE DIEGO of Proyectos Macro, projectFunding =
        «Convenio: <code> — <SUSCRITO>» (and the agreement codes of Contrato/Convenio: neither service contracts
        nor the contracts ending in FN or OS, which the sources write «contrato» and the crosswalk sends to no field;
        Marius, 25/11/2026: those of the inventory that the EML funding text does not mention go to curation). `macro_index`: the «proyecto_macro» index of map_biologico_inventory() (attach_inventory_data()
        finds the Proyectos Macro row only when the cell has a single code).
    """
    dataset = record["dataset"]
    entries = []
    project = dataset.get("project") if isinstance(dataset.get("project"), dict) else {}
    if project:
        title = text(project.get("title"))
        if norm_key(title) == norm_key(text(dataset.get("title"))):
            title = ""
        design = project.get("designDescription") if isinstance(project.get("designDescription"), dict) else {}
        area = project.get("studyAreaDescription") if isinstance(project.get("studyAreaDescription"), dict) else {}
        funding = paragraphs(project.get("funding"))
        for award in as_list(project.get("award")):
            if isinstance(award, dict):
                parts = [(label, text(award.get(key))) for label, key in
                         (("Financiador", "funderName"), ("Identificador del financiador", "funderIdentifier"),
                          ("Número", "awardNumber"), ("Título", "title"), ("URL", "awardUrl"))]
                line = ". ".join(f"{label}: {value}" for label, value in parts if value)
                if line:
                    funding.append(f"Subvención — {line}.")
        entry = {"projectName": title, "projectID": clean(project.get("@id")),
                 "projectDescription": textbox(paragraphs(project.get("abstract"))),
                 "projectDesignDescription": textbox(paragraphs(design.get("description"))),
                 "projectStudyArea": textbox([text(d.get("descriptorValue")) for d in as_list(area.get("descriptor"))
                                              if isinstance(d, dict) and text(d.get("descriptorValue"))]),
                 "projectFunding": textbox(funding)}
        entry = {k: v for k, v in entry.items() if v}
        if entry:
            entries.append(entry)
    biologico = (record["inventory"] or {}).get("biologico") or {}
    cell = [c for c in split_cell(biologico.get("contrato_convenio")) if not PS_CODE.fullmatch(c)]
    agreements = [c for c in cell if not OTHER_CONTRACT.search(c)]
    eml_funding = re.sub(r"\s", "", " ".join(paragraphs(project.get("funding")) if project else [])).upper()
    for code in cell:
        if OTHER_CONTRACT.search(code) and re.sub(r"\s", "", code).upper() not in eml_funding:
            curation.append({"resource": record["name"], "kind": "contract_code", "field": "contractCode",
                             "value": code, "note": "código de contrato del inventario (FN/OS) sin campo en la "
                             "tabla y ausente del texto de financiación del EML"})
    for code in split_cell(biologico.get("proyecto_macro")):
        macro = macro_index.get(code) or {}
        counterpart = clean(macro.get("suscrito"))
        funding = [f"Convenio: {code} — {counterpart}" if counterpart else f"Convenio: {code}"]
        funding += [f"Convenio: {c}" for c in agreements if c != code]
        entry = {"projectShortName": clean(biologico.get("proyecto")), "projectID": code,
                 "projectName": clean(macro.get("nombre_diego")), "projectFunding": textbox(funding)}
        entries.append({k: v for k, v in entry.items() if v})
    return entries


def same_name(a, b):
    """Whether two spellings name the same person: the words of one (without accents, case nor punctuation)
    contain the words of the other, so that «Karina Muñoz Gómez» (inventory) = «Muñoz, Karina» (EML)."""
    words_a, words_b = set(norm_key(a).split()), set(norm_key(b).split())
    shorter = min(words_a, words_b, key=len)
    return len(shorter) >= 2 and (words_a <= words_b or words_b <= words_a) or words_a == words_b


def map_contractors(record):
    """institutional/contractor: service-contract codes (EML funding text + inventory Contrato/Convenio) and
    contractors (EML persons whose position says «contratista» + inventory Contratista if not one of them).
    One contractor and one code → one entry; otherwise names and codes in separate entries (curation)."""
    dataset = record["dataset"]
    project = dataset.get("project") if isinstance(dataset.get("project"), dict) else {}
    biologico = (record["inventory"] or {}).get("biologico") or {}
    codes = []
    for found in [m.group(0) for p in paragraphs(project.get("funding")) for m in PS_CODE.finditer(p)] + \
            [c for c in split_cell(biologico.get("contrato_convenio")) if PS_CODE.fullmatch(c)]:
        code = re.sub(r"\s", "", found).upper()
        if code not in codes:
            codes.append(code)
    names = eml_contractors(dataset)
    contractor = clean(biologico.get("contratista"))
    if contractor and norm_key(contractor) not in FILLERS and not any(same_name(contractor, n) for n in names):
        names.append(contractor)
    if len(names) == 1 and len(codes) == 1:
        return [{"contractCode": codes[0], "contractorName": names[0]}]
    return [{"contractCode": c} for c in codes] + [{"contractorName": n} for n in names]


def map_access(record, tables, curation):
    """institutional/access: accessType; for restricted files (Restricted, Internal open access) the restriction
    reason of the inventory text «Objeto de la restricción» through tablas/restriction_reasons.csv: reason_code
    (decided by the team) or, while it is empty, proposed_reason (Marius, 25/11/2026). A reason from a row whose
    validated cell is empty is listed for curation, as a missing reason; for Restricted, restrictedUntil from
    «Fecha liberación», a missing date listed for curation."""
    access = access_type(record["dataset"])
    entry = {"accessType": access}
    biologico = (record["inventory"] or {}).get("biologico") or {}
    if access in (RESTRICTED, INTERNAL_ACCESS):
        reasons = {clean(r["restriction_text"]): r for r in tables["restriction_reasons"]}
        reason_text = clean(biologico.get("objeto_restriccion"))
        if norm_key(reason_text) in FILLERS | {"nd"}:  # «NA», «ND»: sin texto
            reason_text = ""
        row = reasons.get(reason_text) or {}
        reason = clean(row.get("reason_code")) or clean(row.get("proposed_reason"))
        if reason:
            entry["restrictionJustification"] = reason
        if not reason or not clean(row.get("validated")):
            note = ("sin texto en el inventario" if not reason_text
                    else "texto sin razón en tablas/restriction_reasons.csv" if not reason
                    else "razón no validada (" + ("reason_code" if clean(row.get("reason_code"))
                                                   else "proposed_reason") + "): revisar en la curación")
            curation.append({"resource": record["name"], "kind": "restriction_reason",
                             "field": "restrictionJustification", "value": reason_text, "note": note})
    if access == RESTRICTED:
        raw = clean(biologico.get("fecha_liberacion"))
        date = iso_date(raw)
        if date and len(date) == 10:
            entry["restrictedUntil"] = date
        else:
            curation.append({"resource": record["name"], "kind": "restricted_until", "field": "restrictedUntil",
                             "value": raw, "note": "sin fecha de liberación en el inventario"})
    return entry


def map_institutional(record, tables, macro_index, curation):
    """The institutional block of a record."""
    fields = {"access": map_access(record, tables, curation)}
    projects = map_projects(record, macro_index, curation)
    if projects:
        fields["project"] = projects
    contractors = map_contractors(record)
    if contractors:
        fields["contractor"] = contractors
    acknowledgement = textbox(paragraphs(record["dataset"].get("acknowledgements")))
    if acknowledgement:
        fields["acknowledgement"] = acknowledgement
    return fields


# ---------------------------------------------------------------------------------------------------------------
# Registro completo
# ---------------------------------------------------------------------------------------------------------------

def drop_empty(value):
    """The value without empty strings, empty lists and empty dicts (recursively)."""
    if isinstance(value, dict):
        value = {k: drop_empty(v) for k, v in value.items()}
        return {k: v for k, v in value.items() if v not in ("", [], {}, None)}
    if isinstance(value, list):
        value = [drop_empty(v) for v in value]
        return [v for v in value if v not in ("", [], {}, None)]
    return value


def dataverse_fields(record, tables, identifiers, macro_index):
    # Compared with feature/integracion-ceiba-dataverse-v2 (commit bbdd77d, src/mapeo/ceiba_mapping.py, construir_citation_intermedio()):
    # covers all the crosswalk rows with a source, in the five blocks (citation with author, datasetContact,
    # producer, distributor and contributor; geospatial; biologicalMetadata; externalReferences; institutional),
    # and lists for the curation phase the values left out or given a fallback. author and datasetContact are
    # required: without them Dataverse does not create the dataset.
    """All Dataverse fields of a record: ({block: {field: value}}, curation rows).

    `identifiers`: vocabulary_identifiers(); `macro_index`: the «proyecto_macro» index of the inventory.
    The URLs of the url fields are percent-encoded (quote_urls() of the GeoNetwork mapping).
    """
    curation = []
    citation = map_citation(record, tables, identifiers)
    citation["author"] = map_authors(record, tables["citation_authors_index"], curation)
    parties, notes = map_parties(record, tables["party_roles"])
    citation.update(parties)
    curation += [{"resource": n["resource"], "kind": n["kind"], "field": n["element"],
                  "value": f"{n['name']} — {n['value'] or n['role']}", "note": n["role"]} for n in notes]
    blocks = {"citation": citation, "geospatial": map_geospatial(record, curation),
              "institutional": map_institutional(record, tables, macro_index, curation),
              "externalReferences": {"externalReference": map_external_references(record, curation)},
              "biologicalMetadata": map_biological(record, tables, curation)}
    blocks = {block: drop_empty(quote_urls(fields)) for block, fields in blocks.items()}
    return {block: fields for block, fields in blocks.items() if fields}, curation


def load_options(record, fields):
    """Information for the load, outside the metadata blocks (decision of 06/11/2026): draft (private IPT
    resources are loaded unpublished and listed for curation), access type, licence or custom terms.

    Open access → CC BY-NC 4.0; internal or restricted → no licence, the intellectualRights text as custom terms
    of use, restricted files with file access requests.
    """
    access = fields.get("institutional", {}).get("access", {}).get("accessType")
    options = {"draft": record["ipt_status"] != "PUBLIC", "accessType": access}
    if access == OPEN_ACCESS:
        options["license"] = "CC BY-NC 4.0"
    else:
        options.update(license=None, termsOfUse=rights_text(record["dataset"]) or None)
    return options
