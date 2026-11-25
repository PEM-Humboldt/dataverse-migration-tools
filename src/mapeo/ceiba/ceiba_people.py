"""People and organisations of a Ceiba record → citation/author, producer, datasetContact, distributor,
contributor (crosswalk rows author*, producer*, datasetContact*, distributor*, contributor*; team decisions of
04–06/11/2026, summarised in preparingMigration/ceiba/personas_roles_dataverse.md).

- author: the names written before the year in Ceiba's citation text (additionalMetadata/metadata/gbif/citation),
  as written, in the same order, read from the hand-reviewed table tablas/citation_authors.csv (one row per
  author and dataset; Marius, 25/11/2026). The table was extracted once from the citations of the IPT copy of
  24/11/2026 (rule of the block citation-authors-check of testCeiba/03_mapping.qmd, reviewed by hand); a dataset
  added to Ceiba afterwards needs its rows added by hand (map_authors()).
- producer, datasetContact, distributor, contributor: from the EML elements and roles, by tablas/party_roles.csv;
  a person or organisation appears once per target (field, and contributor type) in a dataset: the first
  occurrence is kept, in the order creator, contact, metadataProvider, then associatedParty, then
  project/personnel.
"""
import re
import unicodedata

from src.mapeo.ceiba.ceiba_source import as_list, clean, text

INSTITUTE_NAME = "Instituto de Investigación de Recursos Biológicos Alexander von Humboldt"
INSTITUTE_ABBREVIATION = "IAvH"
INSTITUTE_URL = "https://www.humboldt.org.co"
INSTITUTE_LOGO = "https://raw.githubusercontent.com/SIB-Colombia/logos/main/socio-SiB-iavh.png"
DEFAULT_CONTACT_EMAIL = "i2d@humboldt.org.co"
EMAIL_TYPO = re.compile(r"@humboldt\.org$", re.IGNORECASE)  # errata frecuente: i2d@humboldt.org
# orden de lectura: la primera aparición de una persona en un destino es la que se conserva
TOP_LEVEL = ("creator", "contact", "metadataProvider")
PROJECT_MEMBER = "Project Member"


def norm_key(value):
    """Comparison key: lower case, without accents or punctuation, single spaces («Pulido-Santacruz» =
    «Pulido Santacruz»)."""
    raw = unicodedata.normalize("NFKD", (value or "").lower())
    raw = "".join(c for c in raw if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", raw).split())


# ---------------------------------------------------------------------------------------------------------------
# Autores: tabla de los nombres escritos antes del año en la cita de Ceiba
# ---------------------------------------------------------------------------------------------------------------

def citation_text(gbif):
    """Ceiba's citation text (str, or the #text of the element with its identifier)."""
    return text(gbif.get("citation"))


def authors_index(rows):
    """{resource: [rows of tablas/citation_authors.csv in author_position order]}."""
    index = {}
    for row in rows:
        if clean(row.get("author_name")):
            index.setdefault(clean(row["resource"]), []).append(row)
    for found in index.values():
        found.sort(key=lambda r: int(r.get("author_position") or 0))
    return index


def map_authors(record, authors, curation):
    """citation/author: [{"authorName"}] from tablas/citation_authors.csv (`authors`: authors_index()), in the order
    of author_position, as written (no affiliation nor identifier at migration, decision of 06/11/2026).

    A dataset whose rows have status «revisar» (doubtful cases: «et al.», citation without a year, incomplete
    names…) is listed for curation. A dataset without rows in the table (added to Ceiba after the extraction)
    gets the Institute as default author (INSTITUTE_NAME, Marius, 25/11/2026) and is listed for curation: its
    rows must be added to the table before the migration.
    """
    found = authors.get(record["name"], [])
    if not found:
        curation.append({"resource": record["name"], "kind": "default_author", "field": "authorName",
                         "value": citation_text(record["gbif"]),
                         "note": "sin filas en tablas/citation_authors.csv: autor por defecto el Instituto; "
                                 "añadir los autores de la cita a la tabla"})
        return [{"authorName": INSTITUTE_NAME}]
    if any(clean(r.get("status")) == "revisar" for r in found):
        curation.append({"resource": record["name"], "kind": "author_review", "field": "authorName",
                         "value": " | ".join(clean(r["author_name"]) for r in found),
                         "note": clean(found[0].get("note")) or "autores por revisar"})
    return [{"authorName": clean(r["author_name"])} for r in found]


# ---------------------------------------------------------------------------------------------------------------
# Personas y organizaciones de los elementos del EML
# ---------------------------------------------------------------------------------------------------------------

def party(element, kind, role=""):
    """One appearance of a person or organisation: {kind, role, name, is_person, affiliation, email}.

    A person's name is «Apellido, Nombre». An appearance without a given name whose surname is the
    organisation name, or without any person name, is the organisation (rule 1 of personas_roles_dataverse.md).
    """
    individual = element.get("individualName") or {}
    given = text(individual.get("givenName")) if isinstance(individual, dict) else ""
    surname = text(individual.get("surName")) if isinstance(individual, dict) else ""
    organisation = text(element.get("organizationName"))
    emails = [clean(e) for e in as_list(element.get("electronicMailAddress")) if clean(e)]
    if given and surname:
        name, is_person = f"{surname}, {given}", True
    elif surname and norm_key(surname) != norm_key(organisation):
        name, is_person = surname, True
    else:
        name, is_person = organisation or surname, False
    return {"kind": kind, "role": clean(role), "name": name, "is_person": is_person,
            "affiliation": organisation if is_person else "",
            "email": EMAIL_TYPO.sub("@humboldt.org.co", emails[0]) if emails else "",
            "position": " ".join(text(p) for p in as_list(element.get("positionName")))}


def appearances(dataset):
    """All appearances in reading order: creator, contact, metadataProvider, associatedParty, project/personnel."""
    found = []
    for kind in TOP_LEVEL:
        found += [party(e, kind) for e in as_list(dataset.get(kind)) if isinstance(e, dict)]
    found += [party(e, "associatedParty", e.get("role") or "") for e in as_list(dataset.get("associatedParty"))
              if isinstance(e, dict)]
    project = dataset.get("project") if isinstance(dataset.get("project"), dict) else {}
    found += [party(e, "personnel", e.get("role") or "") for e in as_list(project.get("personnel"))
              if isinstance(e, dict)]
    return [p for p in found if p["name"]]


def role_targets(party_roles):
    """{(party_type, role): [(target_field, contributor_type)]} from tablas/party_roles.csv (a role of
    project/personnel has two rows: Project Member and the target of the role)."""
    targets = {}
    for row in party_roles:
        key = (row["party_type"], row["role"])
        targets.setdefault(key, []).append((row["target_field"], row["contributor_type"]))
    return targets


def institute_extras(name, prefix):
    """Abbreviation, URL and logo of the Institute, only when the name as written contains «Humboldt» or is
    «IAvH» (comparison without accents nor case; Marius, 10/11/2026)."""
    key = norm_key(name)
    if "humboldt" in key.split() or key == "iavh":
        return {f"{prefix}Abbreviation": INSTITUTE_ABBREVIATION, f"{prefix}URL": INSTITUTE_URL,
                f"{prefix}LogoURL": INSTITUTE_LOGO}
    return {}


def map_parties(record, party_roles):
    """producer, datasetContact, distributor and contributor of a record, plus the contacts that received a
    fallback email (for the curation list).

    Returns ({field: [compound]}, [fallback rows]). Unknown (element, role) pairs are reported as
    ("unknown_role", …) rows in the second list and left out.
    """
    targets = role_targets(party_roles)
    parties = appearances(record["dataset"])
    emails = {}
    for p in parties:  # correo de cada persona u organización en el EML, para los contactos sin correo
        if p["email"]:
            emails.setdefault(norm_key(p["name"]), p["email"])
    seen, notes = set(), []
    fields = {"producer": [], "datasetContact": [], "distributor": [], "contributor": []}
    for p in parties:
        key_role = (p["kind"], p["role"] if p["kind"] in ("associatedParty", "personnel") else "")
        found = targets.get(key_role)
        if found is None:
            notes.append({"resource": record["name"], "kind": "unknown_role", "element": p["kind"], "role": p["role"],
                          "name": p["name"], "value": ""})
            continue
        for target, contributor_type in found:
            key = (target, contributor_type, norm_key(p["name"]))
            if key in seen:
                continue
            seen.add(key)
            if target == "producer":
                entry = {"producerName": p["name"], "producerAffiliation": p["affiliation"]}
                entry.update(institute_extras(p["name"], "producer"))
            elif target == "distributor":
                entry = {"distributorName": p["name"], "distributorAffiliation": p["affiliation"]}
                entry.update(institute_extras(p["name"], "distributor"))
            elif target == "datasetContact":
                email, source = p["email"], "EML"
                if not email:
                    email = emails.get(norm_key(p["name"]))
                    source = "otro elemento del EML"
                if not email:
                    email, source = DEFAULT_CONTACT_EMAIL, "correo de la I2D"
                if source != "EML":
                    notes.append({"resource": record["name"], "kind": "contact_email", "element": p["kind"],
                                  "role": p["role"], "name": p["name"], "value": f"{email} ({source})"})
                entry = {"datasetContactName": p["name"], "datasetContactAffiliation": p["affiliation"],
                         "datasetContactEmail": email}
            else:
                entry = {"contributorType": contributor_type, "contributorName": p["name"]}
            fields[target].append({k: v for k, v in entry.items() if v})
    return {k: v for k, v in fields.items() if v}, notes


CONTRACTOR_POSITION = re.compile(r"contrat[io]sta|contratosta", re.IGNORECASE)
NOT_CONTRACTOR = re.compile(r"supervisor", re.IGNORECASE)


def eml_contractors(dataset):
    """Names of the EML persons whose position says «contratista» (or a variant), except «Supervisor del
    contrato», as «Apellido, Nombre», without repetitions (crosswalk contractorName)."""
    names, seen = [], set()
    for p in appearances(dataset):
        if p["is_person"] and CONTRACTOR_POSITION.search(p["position"]) and not NOT_CONTRACTOR.search(p["position"]):
            if norm_key(p["name"]) not in seen:
                seen.add(norm_key(p["name"]))
                names.append(p["name"])
    return names
