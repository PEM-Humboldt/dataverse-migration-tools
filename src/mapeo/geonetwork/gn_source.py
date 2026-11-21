"""Reading the GeoNetwork harvest written by src/ingest/geonetwork_ingest.py.

The harvest folder (GN_DATA_DIR) holds
xml/<uuid>.json (the ISO 19139 XML converted by xml_to_dict_tree()), attachments/<uuid>.json and
sharing/<uuid>.json; it has no /related, so the relations between records are taken from the XML.

read_record() turns one harvested record into a flat, source-side dict: the values of each variable of
tablas/gn_variables.csv (the names the crosswalk cites), their position, the responsible parties, the links
to other records and the API files. gn_mapping.py applies the crosswalk to that dict.

The tree is read with the tag sets of the harvest (src/ingest/geonetwork_ingest.py), which fix its shape:
an element of LIST_TAGS is always a list, an element of STRING_TAGS is always text, any other element is a
single value. A record that does not follow them stops the reading (children()): the tag must then be added to
LIST_TAGS, and xml/ is converted again by the harvest.
"""
import re
from pathlib import Path

from src.ingest.geonetwork_ingest import LIST_TAGS, STRING_TAGS
from src.utilitarios.files import read_csv, read_json

SERVICE_ID = "gmd:identificationInfo/srv:SV_ServiceIdentification/"
DATA_ID = "gmd:identificationInfo/gmd:MD_DataIdentification/"
PARTY_SECTIONS = {"gmd:contact": "metadata_contact", "gmd:citedResponsibleParty": "cited",
                  "gmd:pointOfContact": "point_of_contact", "gmd:distributorContact": "distributor"}
RESOURCE_CITATION = ("gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/",
                     "gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/")
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def read_variables(path):
    """tablas/gn_variables.csv as {full XML path: [variable names]}, without the api_ variables."""
    by_path = {}
    for row in read_csv(path):
        if not row["name"].startswith("api_"):
            by_path.setdefault(row["full_path"], []).append(row["name"])
    return by_path


def attribute_name(key):
    """Attribute key of xml_to_dict_tree() ('@codeListValue', '@{http://www.w3.org/1999/xlink}href') -> 'codeListValue', 'xlink:href'."""
    name = key[1:]
    if name.startswith("{http://www.w3.org/1999/xlink}"):
        return "xlink:" + name.split("}", 1)[1]
    return name.split("}")[-1]


def children(node, key):
    """The elements `key` of a node of the tree as a list, following LIST_TAGS of the harvest.

    Raises ValueError when the tree does not follow LIST_TAGS: a repeated tag missing from LIST_TAGS, or a
    tag of LIST_TAGS that is not a list (xml/ converted with an older LIST_TAGS).
    """
    child = node.get(key)
    if child is None:
        return []
    if (key in LIST_TAGS) != isinstance(child, list):
        problem = "no es una lista" if key in LIST_TAGS else "está repetida y no está en LIST_TAGS"
        raise ValueError(f"{key} {problem} (src/ingest/geonetwork_ingest.py): corregir LIST_TAGS "
                         "y volver a convertir xml/ con la cosecha")
    return child if key in LIST_TAGS else [child]


def walk(node, path, indexed):
    """Yield (path, indexed path, value, uom) for every text and attribute of the dict tree.

    `path` has no indices, as in gn_variables.csv; `indexed` numbers repeated elements ([1], [2]…), only when
    there are several, like an XPath. Attributes give '<path>/@<name>'. Empty values are skipped.
    """
    if isinstance(node, dict):
        for key, child in node.items():
            if key == "#text":
                if str(child).strip():
                    yield path, indexed, str(child).strip(), str(node.get("@uom", "")).strip()
            elif key.startswith("@"):
                if str(child).strip():
                    name = attribute_name(key)
                    yield f"{path}/@{name}", f"{indexed}/@{name}", str(child).strip(), ""
            elif key in STRING_TAGS:  # siempre texto ("" si el elemento está vacío)
                if child.strip():
                    yield f"{path}/{key}", f"{indexed}/{key}", child.strip(), ""
            else:
                items = children(node, key)
                for i, item in enumerate(items, start=1):
                    step = f"{key}[{i}]" if len(items) > 1 else key
                    yield from walk(item, f"{path}/{key}", f"{indexed}/{step}")
    elif node is not None and str(node).strip():
        yield path, indexed, str(node).strip(), ""


def first_value(node, *keys):
    """Text found by following `keys` in the dict tree (first element of each list), or ''."""
    for key in keys:
        if not isinstance(node, dict):
            return ""
        if key.startswith("@") or key in STRING_TAGS:
            node = node.get(key)
        else:
            items = children(node, key)
            node = items[0] if items else None
    if isinstance(node, dict):
        node = node.get("#text", "")
    return str(node).strip() if node is not None else ""


def find_parties(node, path="gmd:MD_Metadata", indexed="gmd:MD_Metadata", parent=""):
    """One dict per gmd:CI_ResponsibleParty, with its place in the record (section) and its position."""
    parties = []
    if not isinstance(node, dict):
        return parties
    for key, child in node.items():
        if key.startswith("@") or key == "#text" or key in STRING_TAGS:
            continue
        items = children(node, key)
        for i, item in enumerate(items, start=1):
            step = f"{key}[{i}]" if len(items) > 1 else key
            if key == "gmd:CI_ResponsibleParty" and isinstance(item, dict):
                section = PARTY_SECTIONS.get(parent, "other")
                if section == "cited" and not any(path.startswith(c) for c in RESOURCE_CITATION):
                    section = "other"  # citas de las fuentes del linaje, de los tesauros…
                email = next((v for p, _, v, _ in walk(item, "", "")
                              if p.endswith("gmd:electronicMailAddress/gco:CharacterString")), "")
                parties.append({
                    "section": section,
                    "role": first_value(item, "gmd:role", "gmd:CI_RoleCode", "@codeListValue"),
                    "individual_name": first_value(item, "gmd:individualName", "gco:CharacterString"),
                    "organisation_name": first_value(item, "gmd:organisationName", "gco:CharacterString"),
                    "position_name": first_value(item, "gmd:positionName", "gco:CharacterString"),
                    "email": email,
                    "url": first_value(item, "gmd:contactInfo", "gmd:CI_Contact", "gmd:onlineResource",
                                       "gmd:CI_OnlineResource", "gmd:linkage", "gmd:URL"),
                    "position": f"{indexed}/{step}",
                })
            parties += find_parties(item, f"{path}/{key}", f"{indexed}/{step}", key)
    return parties


def read_record(uuid, data_dir, variables_by_path):
    """Source-side record of one record of the harvest folder `data_dir` (GN_DATA_DIR).

    Returns {"uuid", "values", "positions", "units", "parties", "links", "sharing", "attachments", "related"}:
    values, positions and units are lists per variable of gn_variables.csv in document order; links are the
    UUIDs of other records named in the XML (operatesOn, lineage sources, parent, aggregates); related is
    None until related_from_links() (gn_mapping.py) fills it.
    """
    data_dir = Path(data_dir)
    tree = read_json(data_dir / "xml", f"{uuid}.json")
    values, positions, units = {}, {}, {}
    links = {"operates_on": [], "sources": [], "parent": [], "aggregates": []}
    for path, indexed, value, uom in walk(tree, "gmd:MD_Metadata", "gmd:MD_Metadata"):
        names = list(variables_by_path.get(path, []))
        # servicios migrados como conjuntos de datos: las variables CIT/ e ID/ se leen en SRV/
        if SERVICE_ID in path:
            names += variables_by_path.get(path.replace(SERVICE_ID, DATA_ID), [])
        for name in names:
            values.setdefault(name, []).append(value)
            positions.setdefault(name, []).append(indexed)
            units.setdefault(name, []).append(uom)
        found = UUID.search(value)
        if found:
            if "/srv:operatesOn/@" in path:
                links["operates_on"].append(found.group(0))
            elif path.endswith("gmd:LI_Lineage/gmd:source/@uuidref"):
                links["sources"].append(found.group(0))
            elif path == "gmd:MD_Metadata/gmd:parentIdentifier/gco:CharacterString":
                links["parent"].append(found.group(0))
            elif "/gmd:aggregateDataSetIdentifier/" in path and path.endswith("gmd:code/gco:CharacterString"):
                links["aggregates"].append(found.group(0))
    record = {"uuid": uuid, "values": values, "positions": positions,
              "units": {name: u for name, u in units.items() if any(u)},
              "parties": find_parties(tree), "links": {k: list(dict.fromkeys(v)) for k, v in links.items()},
              "related": None}
    for name in ("sharing", "attachments"):
        record[name] = read_json(data_dir / name, f"{uuid}.json")
    return record


def migrated(record, excluded_uuids):
    """True if the record is migrated: not a service-level record (md_scope = service) and not excluded."""
    return record["uuid"] not in excluded_uuids and "service" not in record["values"].get("md_scope", [])
