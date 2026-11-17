"""Functions cited in the crosswalk of the Biocultural platform migration (sheet `crosswalk` of
MigracionBiocultural.xlsx, column `treatment`), with the helpers they need.

Origin: prototype project testBiocultural (11/11/2026), harvest of 07/10/2026. Example code to
start from: organise, rename or rewrite it as dataverse-migration-tools requires.

Field values are in the simple form of the Dataverse API without its wrapper: a primitive field is
a string (or a list of strings if repeatable); a compound field is a dict {child field: value} (or
a list of dicts if repeatable). `fields` means a version's {block: {field: value}}; `i2d_row` is the
dataset's row of sheet `socioecologico`; tables are the rows of sheets `vocabularies` and
`proyectos_macro`.
"""
import re
import unicodedata


# ---------------------------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------------------------

def ascii_lower(text):
    """Lower-case text without accents, for comparisons."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def migrate_date(value):
    """Date in Dataverse form (YYYY, YYYY-MM or YYYY-MM-DD), zero-padded; None if not a date («N/A»)."""
    m = re.fullmatch(r"(\d{4})(?:-(\d{1,2})(?:-(\d{1,2}))?)?", (value or "").strip())
    if not m:
        return None
    return "-".join([m.group(1)] + [part.zfill(2) for part in m.groups()[1:] if part])


# Fillers and test values, compared lower-case without punctuation (n.a -> na, No aplica -> noaplica)
FILLERS = {"na", "noaplica", "estructurado", "prueba", "test"}


def filler_key(text):
    """Comparison key of a filler: lower case, letters and digits only."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def is_filler(text):
    """True if `text` is a filler, a value of another field or a test value (see FILLERS; also «dddd»)."""
    key = filler_key(text or "")
    return key in FILLERS or re.fullmatch(r"d{3,}", key) is not None


# ---------------------------------------------------------------------------------------------
# citation
# ---------------------------------------------------------------------------------------------

def migrate_keywords(entries):
    """citation/keyword of a version.

    `entries`: list of keyword dicts (keywordValue, keywordVocabulary, keywordVocabularyURI,
    keywordTermURI), or None. Returns a new list: an entry without term but with a vocabulary takes the
    vocabulary as its term (the keyword was typed in the wrong box); a term listing several values
    separated by commas or semicolons is split into several entries (each keeps vocabulary and URIs);
    empty entries are dropped. Other «vocabularies» that are not vocabularies are copied as they are.
    """
    migrated = []
    for entry in entries or []:
        e = {k: v.strip() for k, v in entry.items() if isinstance(v, str) and v.strip()}
        if "keywordValue" not in e and "keywordVocabulary" in e:
            e["keywordValue"] = e.pop("keywordVocabulary")
        if "keywordValue" not in e:
            continue
        for part in [p.strip() for p in re.split(r"[,;]", e["keywordValue"]) if p.strip()]:
            migrated.append(dict(e, keywordValue=part))
    return migrated


# Default language of the datasets: all files are in Spanish (decision of 11/11/2026)
DEFAULT_LANGUAGE = "Spanish, Castilian"


def migrate_language(languages):
    """citation/language of a version: the platform's languages, or [DEFAULT_LANGUAGE] if there are none."""
    values = [v for v in languages or [] if v and v.strip()]
    return values or [DEFAULT_LANGUAGE]


def migrate_grant_numbers(entries):
    """citation/grantNumber of a version without test values in grantNumberAgency («dddd», «test»).

    Returns a new list; an entry left without any value is dropped. grantNumber is still copied (the
    target does not use it; curation proposes removing it), and also feeds institutional/project.
    """
    migrated = []
    for entry in entries or []:
        e = {k: v for k, v in entry.items()
             if isinstance(v, str) and v.strip() and not (k == "grantNumberAgency" and is_filler(v))}
        if e:
            migrated.append(e)
    return migrated


# Fixed Institute values for producers and distributors (decision of 11/11/2026, same as Ceiba)
INSTITUTE_ABBREVIATION = "IAvH"
INSTITUTE_URL = "https://www.humboldt.org.co"
INSTITUTE_LOGO = "https://raw.githubusercontent.com/SIB-Colombia/logos/main/socio-SiB-iavh.png"


def is_institute_name(name):
    """True if the name, as written, contains «Humboldt» or is «IAvH» (ignoring accents and case).

    Text in parentheses does not count: «Nombre Apellido (Investigador Instituto Humboldt)» is a
    person, not the Institute.
    """
    text = ascii_lower(re.sub(r"\([^)]*\)", "", name or "")).strip()
    return "humboldt" in text or text == "iavh"


def migrate_institute_parties(entries, compound):
    """citation/producer or citation/distributor with the Institute's fixed values.

    `entries`: list of entries of the compound, or None; `compound`: "producer" or "distributor".
    Entries whose name is the Institute (is_institute_name) get the Institute's abbreviation, website
    and logo, replacing the platform's values; other entries are unchanged.
    """
    migrated = []
    for entry in entries or []:
        e = dict(entry)
        if is_institute_name(e.get(f"{compound}Name")):
            e[f"{compound}Abbreviation"] = INSTITUTE_ABBREVIATION
            e[f"{compound}URL"] = INSTITUTE_URL
            e[f"{compound}LogoURL"] = INSTITUTE_LOGO
        migrated.append(e)
    return migrated


# ---------------------------------------------------------------------------------------------
# geospatial
# ---------------------------------------------------------------------------------------------

def state_table(vocabulary_rows):
    """Department equivalences from the rows of sheet `vocabularies`.

    Returns {source value (spaces reduced): (target field, target value)}, the target field being
    `state`, `city` or `otherGeographicCoverage`.
    """
    return {" ".join(r["source_value"].split()): (r["target_path"].split("/")[-1], r["target_value"].strip())
            for r in vocabulary_rows if r["path"].endswith("geographicCoverage/state")}


def migrate_geographic_coverage(entries, states):
    """geospatial/geographicCoverage of a version.

    `entries`: list of coverage dicts (country, state, city, otherGeographicCoverage), or None;
    `states`: result of state_table. Returns a new list: departments normalised through the table (or
    sent to city/otherGeographicCoverage; places of another country also get state = Other), one entry
    per department or per municipality when a value lists several, «Municipio(s) de» removed, no
    duplicate entries. Raises ValueError for a state value without a row in the table.
    """
    migrated = []
    for entry in entries or []:
        e = {k: " ".join(v.split()) for k, v in entry.items() if isinstance(v, str) and v.strip()}
        state_values = [None]
        if "state" in e:
            source = e.pop("state")
            if source not in states:
                raise ValueError(f"state value without a row in sheet vocabularies: {source!r}")
            target, value = states[source]
            if target == "state":
                state_values = [v.strip() for v in (value or "").split(";") if v.strip()] or [None]
            elif value:
                if target in e:
                    raise ValueError(f"{target} already has a value ({e[target]}); cannot add {value}")
                e[target] = value
                if e.get("country", "Colombia") != "Colombia":
                    state_values = ["Other"]
        cities = [None]
        if "city" in e:
            city = re.sub(r"(?i)^municipios? de\s+", "", e.pop("city")).rstrip(".")
            cities = [re.sub(r"(?i)^municipios? de\s+", "", c).strip(" .")
                      for c in re.split(r",|\s+y\s+", city) if c.strip(" .")]
        for state in state_values:
            for city in cities:
                new = dict(e)
                if state:
                    new["state"] = state
                if city:
                    new["city"] = city
                if new not in migrated:
                    migrated.append(new)
    return migrated


def migrate_geographic_unit(value):
    """geospatial/geographicUnit (single value in the target): several values joined with «; »; None if empty."""
    values = value if isinstance(value, list) else [value]
    joined = "; ".join(" ".join(v.split()) for v in values if v and v.strip())
    return joined or None


# Degrees, minutes and seconds followed by a direction: 77° 16.03''W, 5° 42' 25′'N
DMS = re.compile(r"(\d+(?:\.\d+)?)\s*°\s*(?:(\d+(?:\.\d+)?)\s*['′\"″]*\s*)?(?:(\d+(?:\.\d+)?)\s*['′\"″]*\s*)?([NSEWO])")


def migrate_coordinate(value):
    """One bounding box limit in decimal degrees: decimal comma -> point, degrees/minutes/seconds -> decimal.

    Returns the converted text, or the value unchanged if it has neither form.
    """
    if not isinstance(value, str):
        return value
    text = value.strip()
    if re.fullmatch(r"[+-]?\d+,\d+", text):
        return text.replace(",", ".")
    m = DMS.fullmatch(text)
    if m:
        degrees = float(m.group(1)) + float(m.group(2) or 0) / 60 + float(m.group(3) or 0) / 3600
        return f"{-degrees if m.group(4) in 'SWO' else degrees:.6f}"
    return value


def migrate_bounding_boxes(entries):
    """geospatial/geographicBoundingBox of a version, each limit converted by migrate_coordinate."""
    return [{k: migrate_coordinate(v) for k, v in entry.items()} for entry in entries or []]


# ---------------------------------------------------------------------------------------------
# socialscience
# ---------------------------------------------------------------------------------------------

def vocabulary_table(vocabulary_rows, path):
    """Equivalences of one controlled-vocabulary field from the rows of sheet `vocabularies`.

    `path`: source field (e.g. socialscience/collectionMode). Returns {source value (spaces reduced):
    list of target values}; the list is empty when the value is not migrated.
    """
    return {" ".join(r["source_value"].split()): [v.strip() for v in r["target_value"].split(";") if v.strip()]
            for r in vocabulary_rows if r["path"] == path}


def migrate_vocabulary(values, table):
    """Target values of a controlled-vocabulary field (collectionMode, researchInstrument).

    `values`: a string, a list of strings or None; `table`: result of vocabulary_table. Returns the target
    values of all texts, in order, without repetition. Raises ValueError for a text without a row: add the
    row to sheet `vocabularies` (new values appear when the platform is harvested again).
    """
    migrated = []
    for value in values if isinstance(values, list) else [values]:
        if not isinstance(value, str) or not value.strip():
            continue
        key = " ".join(value.split())
        if key not in table:
            raise ValueError(f"value without a row in sheet vocabularies: {key[:80]!r}")
        migrated += [v for v in table[key] if v not in migrated]
    return migrated


COLLECTION_MODE_LABEL = "Descripción del modo de recolección:"


def migrate_data_collection_situation(situation, collection_modes):
    """socialscience/dataCollectionSituation with the original collectionMode texts (data managers' rule).

    `situation`: the version's dataCollectionSituation text, or None; `collection_modes`: the list of
    collectionMode texts (or one text, or None). Without mode texts, returns `situation` (trimmed); with an
    empty `situation`, the mode texts separated by a blank line; otherwise `situation`, a blank line,
    COLLECTION_MODE_LABEL and the mode texts.
    """
    if not isinstance(collection_modes, list):
        collection_modes = [collection_modes]
    modes = "\n\n".join(t.strip() for t in collection_modes if isinstance(t, str) and t.strip())
    situation = situation.strip() if isinstance(situation, str) and situation.strip() else None
    if not modes:
        return situation
    if situation is None:
        return modes
    return f"{situation}\n\n{COLLECTION_MODE_LABEL} {modes}"


def migrate_data_collectors(value):
    """socialscience/dataCollector: the text split on | and ;, without empty parts."""
    return [part.strip() for part in re.split(r"[|;]", value or "") if part.strip()]


def migrate_operations(value):
    """controlOperations or cleaningOperations: None if the value is a filler or test value, else the text."""
    return None if not value or is_filler(value) else value


def migrate_periods(entries, source, target):
    """citation periods (dateOfCollection or timePeriodCovered) as entries of the socialscience soc_* field.

    The soc_* fields are visible in the new Dataverse, the citation ones hidden: the dates move there and
    citation stays empty (decision of 11/11/2026). `entries`: the version's citation/<source> entries, or
    None; `source`: "dateOfCollection" or "timePeriodCovered"; `target`: "soc_dateOfCollection" or
    "soc_timePeriodCovered". Returns {<target>Start, <target>End} dicts with dates from migrate_date
    (only those with a value); a period without any valid date is dropped.
    """
    migrated = []
    for entry in entries or []:
        e = {f"{target}{part}": migrate_date(entry.get(f"{source}{part}")) for part in ("Start", "End")}
        e = {k: v for k, v in e.items() if v}
        if e:
            migrated.append(e)
    return migrated


# ---------------------------------------------------------------------------------------------
# institutional
# ---------------------------------------------------------------------------------------------

ACCESS_TYPES = {
    "libre a nivel interno y externo": "Fully open access (internal/external)",
    "libre a nivel interno": "Internal open access",
    "restringido temporalmente": "Restricted",
    "restriccion temporal": "Restricted",
}


def migrate_access(terms_of_use):
    """(accessType, notification note) from the access category written in a version's termsOfUse.

    Returns (None, None) if the text does not hold exactly one recognised category (empty, the unedited
    template listing all categories, other text). The note is «Con notificación previa.» or None; it has
    no target field (it stays in the custom terms or the external file, depending on the licence rule).
    """
    lines = []
    for line in (terms_of_use or "").splitlines():
        key = re.sub(r"\s+", " ", ascii_lower(line)).strip(" -.")
        if key:
            lines.append(key)
    if len(lines) != 1:
        return None, None
    key, note = lines[0], None
    if key.endswith(" con notificacion previa"):
        key, note = key[: -len(" con notificacion previa")], "Con notificación previa."
    access = ACCESS_TYPES.get(key)
    return (access, note) if access else (None, None)


def migrate_release_date(availability_status):
    """restrictedUntil: the first date (DD/MM/YYYY or YYYY-MM-DD) in availabilityStatus, as YYYY-MM-DD."""
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})|(\d{4})-(\d{2})-(\d{2})", availability_status or "")
    if not m:
        return None
    if m.group(4):
        return f"{m.group(4)}-{m.group(5)}-{m.group(6)}"
    return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"


def migrate_altered(files):
    """altered: "TRUE" if a file says «anonimi…» in its name or description, "FALSE" otherwise.

    First estimate (decision of 07/10/2026), applied to the files of the dataset's latest version and
    used for all its versions. `files`: list of file dicts (label, description).
    """
    anonymised = any(re.search(r"anonimi", f"{f.get('label') or ''} {f.get('description') or ''}", re.IGNORECASE)
                     for f in files or [])
    return "TRUE" if anonymised else "FALSE"


# Institute internal project number (YY-NNN), alone or inside a text
PROJECT_ID = re.compile(r"(?<![\d-])(\d{2})\s?[-–]\s?(\d{3})(?![\d-])")
# Institute contract (…PS) or agreement (…CE) code
CONTRACT_CODE = re.compile(r"\b\d{2}-\d{2,3}-\d{2,4}-\d{3,4}\s?(PS|CE)\b", re.IGNORECASE)
# Institute service contract code (…PS), with or without spaces («23-22-029-109 PS»)
SERVICE_CONTRACT = re.compile(r"\b\d{2}(?:-\s?[0-9A-Z]+){1,3}\s?PS\b", re.IGNORECASE)


def migrate_projects(grant_numbers):
    """Internal project numbers written in citation/grantNumber, as [{"projectID": "YY-NNN"}, ...].

    Numbers in grantNumberValue, without repetition and in order; values holding a contract (…PS) or
    agreement (…CE) code are skipped, although they contain a number of the same form.
    """
    ids = []
    for g in grant_numbers or []:
        value = g.get("grantNumberValue") or ""
        if CONTRACT_CODE.search(value):
            continue
        for a, b in PROJECT_ID.findall(value):
            if f"{a}-{b}" not in ids:
                ids.append(f"{a}-{b}")
    return [{"projectID": i} for i in ids]


def inventory_parts(value):
    """Parts of an I2D inventory cell holding several values (separated by | ; / or line breaks)."""
    parts = [p.strip(" ,.") for p in re.split(r"[|;/\n]", value or "")]
    return [p for p in parts if p and ascii_lower(p) not in ("na", "n/a")]


def service_contract_codes(text):
    """Service contract codes (…PS) in a text, without spaces, upper case, without repetition, in order."""
    return list(dict.fromkeys(re.sub(r"\s", "", c).upper() for c in SERVICE_CONTRACT.findall(text or "")))


def same_person(a, b):
    """True if all the words of the shorter name (at least two) are in the other one."""
    small, large = sorted((frozenset(re.findall(r"[a-z]+", ascii_lower(a))),
                           frozenset(re.findall(r"[a-z]+", ascii_lower(b)))), key=len)
    return len(small) >= 2 and small <= large


def migrate_institutional_projects(grant_numbers, i2d_row, macro_projects):
    """institutional/project entries of a version (decision of 11/11/2026).

    `grant_numbers`: the version's citation/grantNumber after migrate_grant_numbers, or None; `i2d_row`:
    the dataset's row of sheet `socioecologico`, or None; `macro_projects`: {project number:
    row of sheet `proyectos_macro`}. Returns dicts with projectName, projectShortName, projectID,
    projectDescription and projectFunding (only those with a value):

    1. each grantNumber entry with a project number gives an entry with projectID and, as projectFunding,
       the agency followed by the funding number when it says more than the project number
       («<agency> — <number>»; several entries with the same number: texts joined with «; »);
    2. inventory numbers (column proyecto_macro) not already present give new entries;
    3. each numbered entry found in Proyectos Macro gets NOMBRE CORTO -> projectShortName, NOMBRE DIEGO ->
       projectName, OBJETO -> projectDescription and, if it has no platform funding, SUSCRITO ->
       projectFunding;
    4. grantNumber entries without a project number come last, as funding-only entries (whether they
       belong to a numbered project is decided in curation).
    """
    with_id, without_id = {}, []
    for g in grant_numbers or []:
        agency = (g.get("grantNumberAgency") or "").strip()
        value = (g.get("grantNumberValue") or "").strip()
        ids = [p["projectID"] for p in migrate_projects([g])]
        rest = SERVICE_CONTRACT.sub("", value) if service_contract_codes(value) else value
        rest = re.sub(r"(?i)^\s*(contrato|no\.?|n°)(\s+(contrato|no\.?|n°))*\s*$", "", rest).strip(" ,.-:")
        detail = "" if not rest or rest in ids else rest
        funding = " — ".join(t for t in (agency, detail) if t)
        if ids:
            for i in ids:
                texts = with_id.setdefault(i, [])
                if funding and funding not in texts:
                    texts.append(funding)
        elif funding:
            without_id.append({"projectFunding": funding})
    projects = [{"projectID": i, **({"projectFunding": "; ".join(t)} if t else {})} for i, t in with_id.items()]
    for i in inventory_parts((i2d_row or {}).get("proyecto_macro")):
        if i not in with_id:
            projects.append({"projectID": i})
            with_id[i] = []
    for p in projects:
        info = macro_projects.get(p["projectID"]) or {}
        for field, column in (("projectShortName", "nombre_corto"), ("projectName", "nombre_diego"),
                              ("projectDescription", "objeto"), ("projectFunding", "suscrito")):
            text = (info.get(column) or "").strip()
            if text and field not in p:
                p[field] = text
    return projects + without_id


# Contractor job title inside a data collector text: «…, Contratista IAvH», «… (contratista IAvH)»
CONTRACTOR_JOB = re.compile(r"\s*(?:,|\(|-)\s*contratistas?\b.*$", re.IGNORECASE)
# Parties that can be marked «contratista»: (compound, name subfield, affiliation subfield)
CONTRACTOR_PARTIES = (("author", "authorName", "authorAffiliation"),
                      ("datasetContact", "datasetContactName", "datasetContactAffiliation"),
                      ("producer", "producerName", "producerAffiliation"),
                      ("distributor", "distributorName", "distributorAffiliation"))


def platform_contractors(fields):
    """Names of the people marked «contratista» in a version, once per person, in order.

    «contratista» in the affiliation of an author, contact, producer or distributor (name as written), or
    in a data collector text (the job title part removed). `fields`: the version's {block: {field: value}}.
    """
    names = []
    citation = fields.get("citation", {})
    for compound, name_field, affiliation_field in CONTRACTOR_PARTIES:
        for entry in citation.get(compound) or []:
            name = (entry.get(name_field) or "").strip()
            if name and re.search(r"(?i)contratista", entry.get(affiliation_field) or ""):
                names.append(name)
    for value in migrate_data_collectors(fields.get("socialscience", {}).get("dataCollector")):
        if re.search(r"(?i)contratista", value):
            name = CONTRACTOR_JOB.sub("", value).strip()
            if name:
                names.append(name)
    unique = []
    for name in names:
        if not any(same_person(name, u) for u in unique):
            unique.append(name)
    return unique


def version_texts(value):
    """All strings of a field value (string, list or dict), to search for codes."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [t for v in value.values() for t in version_texts(v)]
    if isinstance(value, list):
        return [t for v in value for t in version_texts(v)]
    return []


def migrate_contractors(fields, i2d_row):
    """institutional/contractor entries of a version: Institute service contracts (…PS) only.

    `fields`: the version's {block: {field: value}}; `i2d_row`: the dataset's I2D inventory row, or None.
    Returns [{"contractorName": ..., "contractCode": ...}, ...] (only keys with a value):

    1. the inventory's …PS codes (column contrato_convenio) paired in order with its contractor names
       (contratista_s, split on | ; / and parentheses); a name that is a person of the version takes the
       platform spelling. A dataset without any …PS code in the inventory gets no inventory contractors
       (its names are agreement counterparts);
    2. people marked «contratista» in the platform not already present;
    3. …PS codes written anywhere in the version not already present, each in its own entry.
    """
    row = i2d_row or {}
    codes = service_contract_codes(row.get("contrato_convenio"))
    names = inventory_parts(re.sub(r"[()]", ";", row.get("contratista_s") or "")) if codes else []
    platform = platform_contractors(fields)
    people = [entry.get(n) for c, n, _ in CONTRACTOR_PARTIES for entry in fields.get("citation", {}).get(c) or []
              if entry.get(n)] + platform
    entries = []
    for i in range(max(len(codes), len(names))):
        name = names[i] if i < len(names) else ""
        name = next((p for p in people if name and same_person(p, name)), name)
        entries.append({"contractorName": name, "contractCode": codes[i] if i < len(codes) else ""})
    for name in platform:
        if not any(e["contractorName"] and same_person(e["contractorName"], name) for e in entries):
            entries.append({"contractorName": name, "contractCode": ""})
    used = {e["contractCode"] for e in entries}
    for text in version_texts(fields):
        for code in service_contract_codes(text):
            if code not in used:
                entries.append({"contractorName": "", "contractCode": code})
                used.add(code)
    return [{k: v for k, v in e.items() if v} for e in entries]


# ---------------------------------------------------------------------------------------------
# externalReferences
# ---------------------------------------------------------------------------------------------

# Target reference type for each DataCite relation type (the others get no type: chosen in curation)
REFERENCE_TYPES = {
    "IsSupplementedBy": "This dataset references",
    "References": "This dataset references",
    "IsCitedBy": "Citation",
    "IsReferencedBy": "Citation",
}


def migrate_publications(publications):
    """externalReferences/externalReference entries from a version's citation/publication.

    Returns dicts with citationText, externalReferenceURL, externalReferenceDOI, externalReferenceOtherId
    (prefixed by its type: «ISBN:…», «handle:…»), externalReferenceType and externalReferenceNote (the
    platform's relation type, or that there was none), only keys with a value, in order. A publication
    without citation, URL or identifier is dropped. citation/publication itself stays empty.
    """
    references = []
    for pub in publications or []:
        get = lambda k: (pub.get(k) or "").strip()
        id_type, id_number = get("publicationIDType").lower(), get("publicationIDNumber")
        ref = {"citationText": get("publicationCitation"), "externalReferenceURL": get("publicationURL")}
        if id_number and id_type == "url" and not ref["externalReferenceURL"]:
            ref["externalReferenceURL"] = id_number
        elif id_number and id_type == "doi":
            ref["externalReferenceDOI"] = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", id_number, flags=re.I)
        elif id_number and id_type != "url":
            ref["externalReferenceOtherId"] = f"{id_type.upper() if id_type in ('isbn', 'issn') else id_type}:{id_number}"
        ref = {k: v for k, v in ref.items() if v}
        if not ref:
            continue
        relation = get("publicationRelationType")
        ref_type = REFERENCE_TYPES.get(relation)
        if ref_type:
            ref["externalReferenceType"] = ref_type
        ref["externalReferenceNote"] = (f"Relación en la plataforma Biocultural: {relation}." if relation
                                        else "Sin tipo de relación en la plataforma Biocultural.")
        references.append(ref)
    return references


# Note of the reference to the copy on the source platform (decision of 11/11/2026)
PLATFORM_COPY_NOTE = ("Página del conjunto de datos en la plataforma Biocultural del Instituto Humboldt, "
                      "de donde se migraron sus metadatos y archivos.")


def migrate_external_references(persistent_id, publications, platform_url):
    """externalReferences of a version: the copy on the source platform, then the publications.

    The first entry is the dataset's page on the platform (`platform_url`, https://biocultural.humboldt.org.co),
    type «External Copy of the dataset», with PLATFORM_COPY_NOTE; then those of migrate_publications.
    """
    copy = {"externalReferenceType": "External Copy of the dataset",
            "externalReferenceURL": f"{platform_url.rstrip('/')}/dataset.xhtml?persistentId={persistent_id}",
            "externalReferenceNote": PLATFORM_COPY_NOTE}
    return [copy] + migrate_publications(publications)
